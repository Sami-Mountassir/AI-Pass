import json
import os
import re
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

SUPPORTED_INTENTS = {
    'summarize',
    'sentiment',
    'analyze',
    'anomaly_detection',
    'decision',
    'translate',
    'generate_code',
    'web_search',
}


def safe_json_parse(text):
    if not isinstance(text, str):
        raise ValueError('Response text is not a string')
    trimmed = text.strip()
    try:
        return json.loads(trimmed)
    except json.JSONDecodeError:
        start = trimmed.find('{')
        end = trimmed.rfind('}')
        if start >= 0 and end >= 0 and end > start:
            try:
                return json.loads(trimmed[start:end+1])
            except json.JSONDecodeError:
                pass
        raise


def normalize_intent(intent):
    if not isinstance(intent, str):
        return 'unknown'
    return intent.strip().lower()


def classify_task(user_input, context=None):
    prompt = """
Classify this request into one of:
summarize, sentiment, analyze, anomaly_detection, decision, translate, generate_code, web_search, unknown

Return ONLY valid JSON:
{
  "intent": "...",
  "confidence": 0.0
}

If you are unsure or the request is irrelevant, use "unknown".
"""
    if context:
        prompt += f"\nContext:\n{context}\n"
    prompt += f"\nInput: {user_input}"

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = safe_json_parse(response.text)
        return {
            "intent": normalize_intent(result.get("intent", "unknown")),
            "confidence": float(result.get("confidence", 0) or 0)
        }
    except Exception as e:
        return {"intent": "unknown", "confidence": 0, "error": str(e)}

def summarize(text):
    prompt = f"Summarize this text in 2-3 sentences:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def sentiment(text):
    prompt = f"Analyze the sentiment of this text. Return JSON with 'sentiment' (positive/negative/neutral) and 'reason'.\n\nText: {text}"
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return safe_json_parse(response.text)
    except Exception as e:
        return {"error": "Sentiment analysis failed", "reason": str(e)}

def analyze_data(text):
    numbers = [int(x) for x in re.findall(r"-?\d+", text)]
    if not numbers:
        return "No numbers found in the input. Please provide numeric data or a CSV with numeric columns."

    return {
        "mean": sum(numbers) / len(numbers),
        "max": max(numbers),
        "min": min(numbers),
        "count": len(numbers),
        "data_points": numbers
    }

def anomaly_detection(text):
    prompt = f"Check this input for any anomalies, suspicious patterns, or outliers. Return JSON with 'is_anomaly' (boolean) and 'findings'.\n\nInput: {text}"
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    try:
        return safe_json_parse(response.text)
    except Exception as e:
        return {"error": "Anomaly detection failed", "reason": str(e)}

def decision(text):
    prompt = f"Based on the following information, provide a clear recommendation or decision with a brief justification:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text


def translate(text):
    prompt = (
        "Translate the following text into English. If the text is already in English, "
        "return a fluent English version only.\n\n"
        f"{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def generate_code(text):
    prompt = (
        "Generate working Python code for the following request. "
        "Return only the code block without extra explanation.\n\n"
        f"{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()


def web_search(text):
    prompt = (
        "You are a virtual search assistant. Based on the query below, provide a "
        "concise summary of likely findings, best guesses, and relevant details. "
        "Do not fabricate sources.\n\n"
        f"Query: {text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

class LongTermMemory:
    def __init__(self, path="memory_store.json"):
        self.path = path
        self.entries = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as handle:
                    self.entries = json.load(handle)
            except Exception:
                self.entries = []

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self.entries, handle, indent=2)
        except Exception:
            pass

    def add(self, text):
        entry = {"text": text, "timestamp": time.time()}
        self.entries.append(entry)
        self._save()

    def get_recent(self, n=3):
        return [entry["text"] for entry in self.entries[-n:]]

    def search(self, query, k=3):
        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored = []
        for entry in self.entries:
            entry_tokens = set(re.findall(r"\w+", entry["text"].lower()))
            overlap = len(query_tokens.intersection(entry_tokens))
            if overlap > 0:
                scored.append((overlap, entry["text"]))
        scored.sort(reverse=True, key=lambda item: item[0])
        return [text for _, text in scored[:k]]

    def clear(self):
        self.entries = []
        self._save()


memory = LongTermMemory()


def run_with_memory(user_input):
    memory.add(user_input)
    recent_context = "\n".join(memory.get_recent(3))
    related_context = "\n".join(memory.search(user_input, k=2))
    full_context = recent_context
    if related_context:
        full_context += "\n\nRelated memory:\n" + related_context
    return run_system(user_input, context=full_context)

def run_system(user_input, context=None):
    # 1. Classify intent
    try:
        intent_info = classify_task(user_input, context)
        intent = intent_info.get("intent", "unknown")
        confidence = min(max(intent_info.get("confidence", 0), 0), 1)
    except Exception as e:
        return {"error": f"Classification failed: {e}", "intent": "unknown", "confidence": 0}

    if intent == "unknown":
        return {
            "intent": "unknown",
            "result": "Could not determine intent.",
            "confidence": confidence
        }

    # 2. Route to expert
    if intent == "summarize":
        result = summarize(user_input)
    elif intent == "sentiment":
        result = sentiment(user_input)
    elif intent == "analyze":
        result = analyze_data(user_input)
    elif intent == "anomaly_detection":
        result = anomaly_detection(user_input)
    elif intent == "decision":
        result = decision(user_input)
    elif intent == "translate":
        result = translate(user_input)
    elif intent == "generate_code":
        result = generate_code(user_input)
    elif intent == "web_search":
        result = web_search(user_input)
    else:
        result = f"Intent '{intent}' not supported"

    # 3. Return structured output
    return {
        "intent": intent,
        "result": result,
        "explanation": f"Intent '{intent}' selected based on input",
        "steps": ["classified intent", "executed function"],
        "confidence": confidence
    }
