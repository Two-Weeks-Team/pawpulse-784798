import json
import os
from typing import List, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()

# -------------------------------------------------------------------
# Configuration – fetched from environment variables
# -------------------------------------------------------------------
API_KEY = os.getenv("DIGITALOCEAN_INFERENCE_KEY")
if not API_KEY:
    raise RuntimeError("DIGITALOCEAN_INFERENCE_KEY environment variable is required")

MODEL = os.getenv("DO_INFERENCE_MODEL", "gpt-5-mini")
# Base URL can be overridden for testing; otherwise use the official endpoint.
BASE_URL = os.getenv(
    "DO_INFERENCE_BASE_URL", "https://api.digitalocean.com/v1/ai"
)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# -------------------------------------------------------------------
# Low‑level helper that talks to the chat/completions endpoint
# -------------------------------------------------------------------
async def _post(messages: List[Dict[str, str]]) -> Dict:
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        return response.json()

# -------------------------------------------------------------------
# Public helpers used by ``routes.py``
# -------------------------------------------------------------------
async def check_symptoms(data: Dict) -> Dict:
    """Ask the LLM to classify a symptom description.

    The model is instructed to respond **only** with JSON of the form::

        {"conditions": [{"name": str, "confidence": float, "urgency": str}, ...]}

    """
    system_prompt = (
        "You are a veterinary AI assistant. Analyze the provided pet metadata and symptom description. "
        "Return a JSON object with a top‑level key 'conditions' containing up to three probable conditions. "
        "Each condition must include 'name' (string), 'confidence' (0‑1 float), and 'urgency' ('low', 'medium', 'high')."
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
    """Ask the model to create a human‑readable health summary.

    Expected output format::

        {"report": "<multi‑line string>"}
    """
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
