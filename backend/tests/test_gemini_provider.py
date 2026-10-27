import json
from types import SimpleNamespace

from google.genai import types

from app.agent.models import Tool
from app.agent.providers.gemini import GeminiProvider


class FakeFunctionCall:
    def __init__(self, name, args):
        self.name = name
        self.args = args


class FakeResponse:
    def __init__(self, text=None, function_calls=None, content="CONTENT"):
        self.text = text
        self.function_calls = function_calls
        self.candidates = [SimpleNamespace(content=content)]


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def make(response):
    client = FakeClient(response)
    return GeminiProvider("test-key", "test-model", client=client), client


USER_HI = [{"role": "user", "content": "hi"}]


def test_text_reply():
    provider, _ = make(FakeResponse(text="Hello"))
    reply = provider.generate("sys", USER_HI, [])
    assert reply.text == "Hello"
    assert reply.tool_calls == []


def test_function_call_reply_keeps_raw_content():
    response = FakeResponse(
        function_calls=[FakeFunctionCall("get_district_risk", {"district_id": "wayanad"})],
        content="RAW-CONTENT",
    )
    provider, _ = make(response)
    reply = provider.generate("sys", USER_HI, [])
    assert reply.text is None
    assert reply.tool_calls[0].name == "get_district_risk"
    assert reply.tool_calls[0].args == {"district_id": "wayanad"}
    assert reply.raw == "RAW-CONTENT"


def test_model_prompt_and_config_are_passed():
    provider, client = make(FakeResponse(text="ok"))
    provider.generate("be calm", USER_HI, [])
    call = client.models.calls[0]
    assert call["model"] == "test-model"
    assert "be calm" in str(call["config"].system_instruction)
    assert call["config"].automatic_function_calling.disable is True


def test_tools_become_function_declarations():
    tools = [
        Tool(
            "with_args",
            "d",
            {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            lambda x: x,
        ),
        Tool("no_args", "d", {"type": "object", "properties": {}}, lambda: 1),
    ]
    provider, client = make(FakeResponse(text="ok"))
    provider.generate("sys", USER_HI, tools)
    decls = client.models.calls[0]["config"].tools[0].function_declarations
    assert [d.name for d in decls] == ["with_args", "no_args"]
    assert decls[0].parameters_json_schema["required"] == ["x"]
    assert decls[1].parameters_json_schema is None


def test_history_uses_raw_and_groups_tool_results():
    raw = types.Content(role="model", parts=[types.Part.from_text(text="RAW")])
    history = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "tool_calls": [{"name": "a", "args": {}}, {"name": "b", "args": {}}],
            "raw": raw,
        },
        {"role": "tool", "name": "a", "content": json.dumps({"result": 1})},
        {"role": "tool", "name": "b", "content": json.dumps({"result": 2})},
    ]
    provider, client = make(FakeResponse(text="ok"))
    provider.generate("sys", history, [])
    contents = client.models.calls[0]["contents"]
    assert [c.role for c in contents] == ["user", "model", "user"]
    assert contents[1] is raw
    assert len(contents[2].parts) == 2
    assert contents[2].parts[0].function_response.name == "a"


def test_tool_call_without_raw_is_rebuilt():
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "tool_calls": [{"name": "a", "args": {"x": 1}}]},
    ]
    provider, client = make(FakeResponse(text="ok"))
    provider.generate("sys", history, [])
    part = client.models.calls[0]["contents"][1].parts[0]
    assert part.function_call.name == "a"
    assert part.function_call.args == {"x": 1}