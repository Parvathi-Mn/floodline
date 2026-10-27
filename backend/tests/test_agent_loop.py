import json

from app.agent.loop import run_turn
from app.agent.models import ProviderReply, Tool, ToolCall
from app.agent.prompt_loader import build_system_prompt

FALLBACK = "Sorry, trouble right now. If in danger, call 112."


class FakeProvider:
    """Returns pre-scripted replies, one per generate() call."""

    def __init__(self, replies):
        self.replies = list(replies)

    def generate(self, system_prompt, messages, tools):
        return self.replies.pop(0)


class AlwaysToolCall:
    def generate(self, system_prompt, messages, tools):
        return ProviderReply(tool_calls=[ToolCall("get_risk", {"district": "wayanad"})])


def risk_tool():
    return Tool(
        name="get_risk",
        description="Get the current flood risk level for a district.",
        parameters={
            "type": "object",
            "properties": {"district": {"type": "string"}},
            "required": ["district"],
        },
        fn=lambda district: {"district": district, "level": "high"},
    )


def run(provider, tools=None, text="hello"):
    history = []
    answer = run_turn(provider, "sys", history, text, tools or [], FALLBACK)
    return answer, history


def test_direct_answer_without_tools():
    answer, history = run(FakeProvider([ProviderReply(text="Hi!")]))
    assert answer == "Hi!"
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_tool_result_is_fed_back_to_model():
    provider = FakeProvider(
        [
            ProviderReply(tool_calls=[ToolCall("get_risk", {"district": "wayanad"})]),
            ProviderReply(text="Risk is high."),
        ]
    )
    answer, history = run(provider, [risk_tool()])
    assert answer == "Risk is high."
    tool_msg = next(m for m in history if m["role"] == "tool")
    assert json.loads(tool_msg["content"])["result"]["level"] == "high"


def test_unknown_tool_becomes_error_not_crash():
    provider = FakeProvider(
        [
            ProviderReply(tool_calls=[ToolCall("does_not_exist")]),
            ProviderReply(text="Data unavailable."),
        ]
    )
    answer, history = run(provider, [risk_tool()])
    assert answer == "Data unavailable."
    tool_msg = next(m for m in history if m["role"] == "tool")
    assert "unknown tool" in tool_msg["content"]


def test_tool_exception_becomes_error_not_crash():
    def broken(district):
        raise RuntimeError("secret internal detail")

    tool = Tool("get_risk", "d", {"type": "object", "properties": {}}, broken)
    provider = FakeProvider(
        [
            ProviderReply(tool_calls=[ToolCall("get_risk", {"district": "x"})]),
            ProviderReply(text="Data unavailable."),
        ]
    )
    answer, history = run(provider, [tool])
    assert answer == "Data unavailable."
    tool_msg = next(m for m in history if m["role"] == "tool")
    assert "RuntimeError" in tool_msg["content"]
    assert "secret internal detail" not in tool_msg["content"]


def test_endless_tool_calls_return_fallback():
    answer, _ = run(AlwaysToolCall(), [risk_tool()])
    assert answer == FALLBACK


def test_empty_model_reply_returns_fallback():
    answer, _ = run(FakeProvider([ProviderReply(text=None)]))
    assert answer == FALLBACK


def test_prompt_includes_emergency_numbers():
    prompt = build_system_prompt("v1", "112 (national emergency)")
    assert "112 (national emergency)" in prompt
    assert "{{" not in prompt

class FailingProvider:
    def generate(self, system_prompt, messages, tools):
        raise RuntimeError("quota exceeded: secret detail")


def test_provider_failure_returns_fallback_not_crash():
    answer, history = run(FailingProvider())
    assert answer == FALLBACK
    assert history[-1] == {"role": "assistant", "content": FALLBACK}


def test_provider_failure_does_not_leak_details():
    answer, history = run(FailingProvider())
    assert "secret detail" not in answer
    assert "secret detail" not in str(history)


def test_raw_provider_data_is_kept_with_tool_calls():
    provider = FakeProvider(
        [
            ProviderReply(
                tool_calls=[ToolCall("get_risk", {"district": "wayanad"})],
                raw="RAW-1",
            ),
            ProviderReply(text="Risk is high."),
        ]
    )
    _, history = run(provider, [risk_tool()])
    tool_call_msg = next(m for m in history if m.get("tool_calls"))
    assert tool_call_msg["raw"] == "RAW-1"