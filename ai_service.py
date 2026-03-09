import json
import os
import re
from typing import List, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
if not API_KEY:
    API_KEY = "missing"

MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
BASE_URL = os.getenv("DO_INFERENCE_BASE_URL", "https://inference.do-ai.run/v1")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def _extract_json(text: str) -> str:
    """Extract JSON from LLM response that may contain markdown code blocks."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


async def _post(messages: List[Dict[str, str]]) -> Dict:
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 512,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()


async def check_symptoms(data: Dict) -> Dict:
    system_prompt = (
        "You are a veterinary AI assistant. Analyze the provided pet metadata and symptom description. "
        "Return a JSON object with a top-level key 'conditions' containing up to three probable conditions. "
        "Each condition must include 'name' (string), 'confidence' (0-1 float), and 'urgency' ('low', 'medium', 'high'). "
        "Return ONLY valid JSON, no extra text."
    )
    user_content = json.dumps(data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    try:
        raw = await _post(messages)
        content = raw["choices"][0]["message"]["content"]
        cleaned = _extract_json(content)
        return json.loads(cleaned)
    except Exception:
        # Fallback: return reasonable defaults instead of crashing
        return {
            "conditions": [
                {
                    "name": "General checkup recommended",
                    "confidence": 0.5,
                    "urgency": "low",
                }
            ],
            "note": "AI analysis temporarily unavailable, please consult your veterinarian",
        }


async def generate_report(data: Dict) -> Dict:
    system_prompt = (
        "You are a veterinary report generator. Using the supplied pet information and health log "
        "entries, produce a concise, friendly health summary report. Return JSON with a single key "
        "'report' containing the full text. Return ONLY valid JSON, no extra text."
    )
    user_content = json.dumps(data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    try:
        raw = await _post(messages)
        content = raw["choices"][0]["message"]["content"]
        cleaned = _extract_json(content)
        return json.loads(cleaned)
    except Exception:
        # Fallback: return reasonable defaults instead of crashing
        return {
            "report": "Health report generation is temporarily unavailable. Based on the provided data, we recommend scheduling a routine veterinary checkup.",
            "note": "AI report temporarily unavailable",
        }
