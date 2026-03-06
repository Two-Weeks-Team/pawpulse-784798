import json
import os
from typing import List, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
if not API_KEY:
    raise RuntimeError("DIGITALOCEAN_INFERENCE_KEY environment variable is required")

MODEL = os.getenv("DO_INFERENCE_MODEL", "openai-gpt-oss-120b")
BASE_URL = os.getenv("DO_INFERENCE_BASE_URL", "https://inference.do-ai.run/v1")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


async def _post(messages: List[Dict[str, str]]) -> Dict:
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 512,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()


async def check_symptoms(data: Dict) -> Dict:
    system_prompt = (
        "You are a veterinary AI assistant. Analyze the provided pet metadata and symptom description. "
        "Return a JSON object with a top-level key 'conditions' containing up to three probable conditions. "
        "Each condition must include 'name' (string), 'confidence' (0-1 float), and 'urgency' ('low', 'medium', 'high')."
    )
    user_content = json.dumps(data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    raw = await _post(messages)
    try:
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to parse AI response for symptom check: {exc}")


async def generate_report(data: Dict) -> Dict:
    system_prompt = (
        "You are a veterinary report generator. Using the supplied pet information and health log "
        "entries, produce a concise, friendly health summary report. Return JSON with a single key "
        "'report' containing the full text."
    )
    user_content = json.dumps(data)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    raw = await _post(messages)
    try:
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)
    except (KeyError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to parse AI response for report generation: {exc}")
