"""Chat orchestration: in-memory sessions, plus prompt and fallback text from client config."""
import threading
from typing import Any

from app.agent.loop import run_turn
from app.agent.models import LLMProvider, Tool
from app.agent.prompt_loader import build_system_prompt
from app.config import Client

# Demo limit: a conversation longer than this is reset (see docs/limitations).
MAX_HISTORY_MESSAGES = 60


def emergency_numbers_text(client: Client) -> str:
    return "\n".join(f"- {n.name}: {n.number}" for n in client.emergency_numbers)


def fallback_message(client: Client) -> str:
    """Safe message used when the model fails. Numbers come from the client config."""
    numbers = ", ".join(f"{n.name} {n.number}" for n in client.emergency_numbers)
    return (
        "Sorry, I'm having trouble right now. "
        f"If anyone is in danger, call now: {numbers}."
    )


class SessionStore:
    """Chat histories kept in memory. Lost on restart, which is fine for a demo."""

    def __init__(self, max_sessions: int = 1000) -> None:
        self._histories: dict[str, list[dict[str, Any]]] = {}
        self._lock = threading.Lock()
        self._max_sessions = max_sessions

    def get(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            if (
                session_id not in self._histories
                and len(self._histories) >= self._max_sessions
            ):
                del self._histories[next(iter(self._histories))]  # drop the oldest
            return self._histories.setdefault(session_id, [])


def handle_chat(
    provider: LLMProvider,
    client: Client,
    tools: list[Tool],
    history: list[dict[str, Any]],
    message: str,
    prompt_version: str,
) -> str:
    if len(history) > MAX_HISTORY_MESSAGES:
        history.clear()
    system_prompt = build_system_prompt(prompt_version, emergency_numbers_text(client))
    return run_turn(
        provider, system_prompt, history, message, tools, fallback_message(client)
    )