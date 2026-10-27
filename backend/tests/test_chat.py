import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main_module
from app.agent.models import ProviderReply, ToolCall
from app.chat import MAX_HISTORY_MESSAGES, SessionStore, fallback_message, handle_chat
from app.config import load_client
from app.main import app, get_provider, get_sessions, get_settings, get_weather
from app.settings import Settings, SettingsError
from app.weather import Rainfall


class ScriptedProvider:
    """Returns pre-scripted replies and records what it was sent."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.system_prompts = []
        self.message_counts = []
        self.last_messages = []

    def generate(self, system_prompt, messages, tools):
        self.system_prompts.append(system_prompt)
        self.message_counts.append(len(messages))
        self.last_messages = messages
        return self.replies.pop(0)


class FailingProvider:
    def generate(self, system_prompt, messages, tools):
        raise RuntimeError("quota exceeded: secret detail")


@pytest.fixture
def api():
    store = SessionStore()
    app.dependency_overrides[get_settings] = lambda: Settings(
        llm_api_key="test-key", llm_model="test-model"
    )
    app.dependency_overrides[get_weather] = lambda: (
        lambda lat, lon: Rainfall(past_5d_mm=100.0, peak_forecast_day_mm=130.0)
    )
    app.dependency_overrides[get_sessions] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def use_provider(provider):
    app.dependency_overrides[get_provider] = lambda: provider


def test_chat_returns_reply_and_session_id(api):
    use_provider(ScriptedProvider([ProviderReply(text="Hello!")]))
    out = api.post("/api/chat", json={"message": "hi"}).json()
    assert out["reply"] == "Hello!"
    assert out["session_id"]


def test_session_history_is_kept(api):
    provider = ScriptedProvider([ProviderReply(text="one"), ProviderReply(text="two")])
    use_provider(provider)
    first = api.post("/api/chat", json={"message": "a"}).json()
    api.post("/api/chat", json={"message": "b", "session_id": first["session_id"]})
    assert provider.message_counts == [1, 3]


def test_new_session_without_id_each_time(api):
    use_provider(ScriptedProvider([ProviderReply(text="x"), ProviderReply(text="y")]))
    a = api.post("/api/chat", json={"message": "hi"}).json()["session_id"]
    b = api.post("/api/chat", json={"message": "hi"}).json()["session_id"]
    assert a != b


def test_system_prompt_uses_numbers_from_config(api):
    provider = ScriptedProvider([ProviderReply(text="ok")])
    use_provider(provider)
    api.post("/api/chat", json={"message": "hi"})
    assert "112" in provider.system_prompts[0]
    assert "{{" not in provider.system_prompts[0]


def test_provider_failure_returns_fallback_with_numbers(api):
    use_provider(FailingProvider())
    response = api.post("/api/chat", json={"message": "help"})
    assert response.status_code == 200
    assert "112" in response.json()["reply"]
    assert "secret detail" not in response.text


def test_chat_runs_the_real_risk_tool(api):
    provider = ScriptedProvider(
        [
            ProviderReply(
                tool_calls=[ToolCall("get_district_risk", {"district_id": "wayanad"})]
            ),
            ProviderReply(text="Risk is high."),
        ]
    )
    use_provider(provider)
    out = api.post("/api/chat", json={"message": "Is Wayanad safe?"}).json()
    assert out["reply"] == "Risk is high."
    tool_msg = next(m for m in provider.last_messages if m["role"] == "tool")
    assert '"level": "high"' in tool_msg["content"]


def test_empty_or_blank_message_is_rejected(api):
    use_provider(ScriptedProvider([]))
    assert api.post("/api/chat", json={"message": ""}).status_code == 422
    assert api.post("/api/chat", json={"message": "   "}).status_code == 422


def test_missing_settings_give_503_without_details(monkeypatch):
    def boom():
        raise SettingsError("Missing required settings in .env: LLM_API_KEY")

    monkeypatch.setattr(main_module, "_load_settings_cached", boom)
    with pytest.raises(HTTPException) as err:
        main_module.get_settings()
    assert err.value.status_code == 503
    assert "LLM_API_KEY" not in err.value.detail


def test_session_store_evicts_oldest():
    store = SessionStore(max_sessions=2)
    store.get("a").append({"role": "user", "content": "x"})
    store.get("b")
    store.get("c")
    assert store.get("a") == []


def test_overlong_history_is_reset():
    client = load_client("kerala")
    history = [{"role": "user", "content": "x"}] * (MAX_HISTORY_MESSAGES + 1)
    provider = ScriptedProvider([ProviderReply(text="ok")])
    handle_chat(provider, client, [], history, "hello", "v1")
    assert len(history) == 2


def test_fallback_message_lists_config_numbers():
    text = fallback_message(load_client("kerala"))
    assert "112" in text and "108" in text