# AI-Pass: Autonomous Task Agent

A comprehensive, context-aware autonomous agent powered by Google Gemini 2.5 Flash. AI-Pass classifies user intent, maintains conversational memory, and executes specialized modules for text, data, and code.

## 🚀 Live Link & Repository
- **Live App:** https://ai-pass-ugtw6atab54vvan8gn3fxj.streamlit.app/
- **GitHub Repo:** https://github.com/Sami-Mountassir/AI-Pass

---

## 🏗️ Architecture
AI-Pass follows a **Modular Pipeline Architecture** consisting of three main layers:

1.  **Frontend (Streamlit)**: A responsive web interface that handles user input (text, PDF, CSV) and renders multi-modal outputs (text, JSON, interactive charts).
2.  **Orchestration Layer (Backend Pipeline)**:
    *   **Memory Manager**: Tracks a 3-step sliding window of conversation history.
    *   **Intent Classifier**: An LLM-based router that converts natural language into structured JSON commands.
3.  **Expert Modules**: A library of specialized functions (AI and Rule-based) that execute specific tasks.

---

## 🧠 How the System Understands Tasks
The system uses **Few-Shot Intent Classification**. When a user provides input, the "Manager" (Gemini 2.5 Flash) analyzes the text against a schema of 8 supported intents.

Instead of returning a conversational response immediately, the LLM is forced to output a **Structured JSON Object**:
```json
{
  "intent": "summarize",
  "confidence": 0.98
}
```
This allows the code to programmatically route the request to the correct expert module with high precision.

---

## ⚙️ How Execution Works
The execution follows a **2-Stage Pipeline**:

1.  **Stage 1: Classification**: The input is enriched with memory context and sent to the classifier to determine the `intent`.
2.  **Stage 2: Expert Routing**:
    *   The `run_system` function receives the intent.
    *   It triggers a specific Python function (e.g., `translate()` or `analyze_data()`).
    *   The result is packaged into a "Response Package" containing metadata (steps taken, confidence level) and the actual output.

---

## 🤖 AI vs. 📐 Rule-Based
AI-Pass leverages the best of both worlds:

| Feature | Type | Why? |
| :--- | :--- | :--- |
| **Summarization** | AI | Requires semantic understanding of language. |
| **Sentiment Analysis** | AI | Interprets emotional tone and nuance. |
| **Code Generation** | AI | Maps logic descriptions to syntax. |
| **Web Search** | AI | Summarizes likely findings and provides concise query results. |
| **Translation** | AI | Converts text to fluent English with context-aware quality. |
| **Data Analysis** | **Rule-Based** | **Precision.** AI often "hallucinates" math. Our system parses raw integers and uses Python's math engine for 100% accuracy on mean, max, and min. |
| **Memory Management** | Hybrid | A file-backed memory store persists recent inputs while preparing the app for future vector search. |

---

## 📈 What’s new in this version
- Added support for **translate**, **generate_code**, and **web_search** intents.
- Improved backend error handling and JSON parsing for safer Gemini responses.
- Enhanced CSV and PDF upload support with file previews and structured extraction.
- Added a simple persistent memory store in `memory_store.json` as a stepping stone to vector search.
