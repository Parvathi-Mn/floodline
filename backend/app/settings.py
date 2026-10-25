"""App settings, read from the repo-root .env file (or real environment variables)."""
import os
from collections.abc import Mapping
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr

# settings.py -> app -> backend -> repo root
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
REQUIRED = ("LLM_API_KEY", "LLM_MODEL")


class SettingsError(Exception):
    """A required setting is missing. The message never contains secret values."""


class Settings(BaseModel):
    llm_api_key: SecretStr  # prints as ********** in logs and repr
    llm_model: str
    client_id: str = "kerala"
    prompt_version: str = "v1"


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load settings. Pass `environ` in tests; otherwise read .env and os.environ."""
    if environ is None:
        load_dotenv(ENV_PATH)  # does not override variables already set
        environ = os.environ

    missing = [name for name in REQUIRED if not environ.get(name, "").strip()]
    if missing:
        raise SettingsError(f"Missing required settings in .env: {', '.join(missing)}")

    return Settings(
        llm_api_key=environ["LLM_API_KEY"].strip(),
        llm_model=environ["LLM_MODEL"].strip(),
        client_id=environ.get("CLIENT_ID", "kerala").strip(),
        prompt_version=environ.get("PROMPT_VERSION", "v1").strip(),
    )