import json
import os
import re
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ====================== API KEY ======================
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in Streamlit Secrets or .env")

# ====================== GEMINI CLIENT ======================
import google.genai as genai

client = genai.Client(api_key=api_key)
MODEL = "gemini-1.5-flash"

def generate_content(prompt: str, json_mode: bool = False):
    try:
        if json_mode:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                generation_config={"response_mime_type": "application/json"}
            )
        else:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini API Error: {str(e)}")
        raise

# ====================== CLASSIFIER ======================
def classify_task(user_input, context=None):
    prompt = f"""
Classify this request into one of these intents only:
summarize, sentiment, analyze, anomaly_detection, decision, translate, generate_code, web_search

Return ONLY JSON like this:
{{"intent": "summarize", "confidence": 0.95}}

Context: {context or "None"}
Request: {user_input}
"""
    try:
        raw_text = generate_content(prompt, json_mode=True)
        result = json.loads(raw_text)
        return {
            "intent": result.get("intent", "unknown").strip().lower(),
            "confidence": float(result.get("confidence", 0))
        }
    except Exception as e:
        return {"intent": "unknown", "confidence": 0, "error": str(e)}

# ====================== EXPERT FUNCTIONS ======================
def summarize(text):
    prompt = f"Summarize this text in 2-3 sentences:\n\n{text}"
    return generate_content(prompt)

def sentiment(text):
    prompt = f'Analyze sentiment. Return only JSON: {{"sentiment": "positive/negative/neutral", "reason": "..."}}\n\n{text}'
    try:
        raw = generate_content(prompt, json_mode=True)
        return json.loads(raw)
    except:
        return {"sentiment": "neutral", "reason": "Analysis failed"}

def analyze_data(text):
    numbers = [int(x) for x in re.findall(r"-?\d+", text)]
    if not numbers:
        return "No numbers found."
    return {
        "mean": sum(numbers) / len(numbers),
        "max": max(numbers),
        "min": min(numbers),
        "count": len(numbers),
        "data_points": numbers
    }

def anomaly_detection(text):
    prompt = f'Check for anomalies. Return only JSON: {{"is_anomaly": true/false, "findings": "..."}}\n\n{text}'
    try:
        raw = generate_content(prompt, json_mode=True)
        return json.loads(raw)
    except:
        return {"is_anomaly": False, "findings": "Could not analyze"}

def decision(text):
    prompt = f"Give a clear decision/recommendation with justification:\n\n{text}"
    return generate_content(prompt)

def translate(text):
    prompt = f"Translate to natural English:\n\n{text}"
    return generate_content(prompt)

def generate_code(text):
    prompt = f"Write clean Python code only. No explanations:\n\n{text}"
    return generate_content(prompt)

def web_search(text):
    prompt = f"Give concise summary of what a web search for this would return:\n\n{text}"
    return generate_content(prompt)

# ====================== MEMORY ======================
class LongTermMemory:
    def __init__(self, path="memory_store.json"):
        self.path = path
        self.entries = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except:
                self.entries = []

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2)
        except:
            pass

    def add(self, text):
        self.entries.append({"text": text, "timestamp": time.time()})
        self._save()

    def get_recent(self, n=3):
        return [e["text"] for e in self.entries[-n:]]

    def clear(self):
        self.entries = []
        self._save()

memory = LongTermMemory()

# ====================== MAIN PIPELINE ======================
def run_with_memory(user_input):
    memory.add(user_input)
    context = "\n".join(memory.get_recent(3))
    return run_system(user_input, context)

def run_system(user_input, context=None):
    intent_info = classify_task(user_input, context)
    intent = intent_info.get("intent", "unknown")
    confidence = min(max(intent_info.get("confidence", 0), 0), 1)

    if intent == "unknown":
        return {"intent": "unknown", "result": "Could not determine intent.", "confidence": confidence}

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
        result = f"Intent '{intent}' not supported yet."

    return {
        "intent": intent,
        "result": result,
        "confidence": confidence,
        "steps": ["classified intent", "executed module"]
    }
