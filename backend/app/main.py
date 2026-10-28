from functools import lru_cache
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, StringConstraints

from .agent.providers.gemini import GeminiProvider
from .agent.tools import build_tools
from .chat import SessionStore, contact_list, handle_chat
from .config import Client, load_client
from .risk import RiskResult, compute_risk
from .settings import Settings, SettingsError, load_settings
from .weather import WeatherError, fetch_rainfall

app = FastAPI(title="Floodline API", version="0.2.0")


@lru_cache
def get_client() -> Client:
    return load_client("kerala")


def get_weather():
    return fetch_rainfall


@lru_cache
def _load_settings_cached() -> Settings:
    return load_settings()


def get_settings() -> Settings:
    try:
        return _load_settings_cached()
    except SettingsError as e:
        # Don't repeat the details to the caller; they are in the server log.
        raise HTTPException(503, "Chat is not configured on this server") from e


@lru_cache
def get_provider() -> GeminiProvider:
    settings = get_settings()
    return GeminiProvider(settings.llm_api_key.get_secret_value(), settings.llm_model)


@lru_cache
def get_sessions() -> SessionStore:
    return SessionStore()


def get_tools(client: Client = Depends(get_client), weather=Depends(get_weather)):
    return build_tools(client, weather)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/districts")
def districts(client: Client = Depends(get_client)):
    return client.districts


@app.get("/api/risk/{district_id}", response_model=RiskResult)
def risk(
    district_id: str,
    client: Client = Depends(get_client),
    weather=Depends(get_weather),
):
    district = client.get_district(district_id)
    if district is None:
        raise HTTPException(404, f"Unknown district: {district_id}")
    try:
        rain = weather(district.lat, district.lon)
    except WeatherError as e:
        raise HTTPException(
            503, f"Weather data unavailable. Emergency contacts: {contact_list(client)}"
        ) from e


class ChatRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    session_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    client: Client = Depends(get_client),
    settings: Settings = Depends(get_settings),
    provider=Depends(get_provider),
    tools=Depends(get_tools),
    sessions: SessionStore = Depends(get_sessions),
):
    session_id = body.session_id or uuid4().hex
    history = sessions.get(session_id)
    reply = handle_chat(
        provider, client, tools, history, body.message, settings.prompt_version
    )
    return ChatResponse(session_id=session_id, reply=reply)


# Serve the chat page at "/". This MUST stay last: a mount at "/" matches every
# URL, so anything registered after it would never be reached.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")