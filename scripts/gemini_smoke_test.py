"""Send one message to Gemini to check that the key and model work."""
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

api_key = os.environ.get("LLM_API_KEY")
model = os.environ.get("LLM_MODEL")
if not api_key or not model:
    raise SystemExit("LLM_API_KEY or LLM_MODEL is missing in .env")

client = genai.Client(api_key=api_key)
try:
    response = client.models.generate_content(
        model=model,
        contents="Reply with one short sentence: what is a flood warning?",
    )
    print("Model replied:", response.text)
except Exception as exc:  # noqa: BLE001 (smoke test: show a short error, never the key)
    print("Call failed:", type(exc).__name__, getattr(exc, "code", ""))