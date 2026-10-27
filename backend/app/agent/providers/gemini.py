"""Gemini provider: translates the agent's message format to and from google-genai."""
import json
from typing import Any

from google import genai
from google.genai import types

from app.agent.models import ProviderReply, Tool, ToolCall


class GeminiProvider:
    def __init__(self, api_key: str, model: str, client: Any = None) -> None:
        self.model = model
        self.client = client or genai.Client(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[Tool],
    ) -> ProviderReply:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(function_declarations=[_declaration(t) for t in tools])]
            if tools
            else None,
            # We run the tool loop ourselves (see agent/loop.py).
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=_to_contents(messages),
            config=config,
        )
        calls = [
            ToolCall(name=fc.name, args=dict(fc.args or {}))
            for fc in (response.function_calls or [])
        ]
        # Gemini 3 needs its own function-call message sent back unchanged
        # (it carries thought signatures), so keep it as `raw`.
        raw = response.candidates[0].content if response.candidates else None
        return ProviderReply(
            text=None if calls else response.text,
            tool_calls=calls,
            raw=raw,
        )


def _declaration(tool: Tool) -> types.FunctionDeclaration:
    has_params = bool(tool.parameters.get("properties"))
    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description,
        parameters_json_schema=tool.parameters if has_params else None,
    )


def _to_contents(messages: list[dict[str, Any]]) -> list[types.Content]:
    contents: list[types.Content] = []
    tool_results: list[types.Part] = []  # consecutive tool results share one Content

    def flush() -> None:
        if tool_results:
            contents.append(types.Content(role="user", parts=list(tool_results)))
            tool_results.clear()

    for m in messages:
        role = m["role"]
        if role == "tool":
            tool_results.append(
                types.Part.from_function_response(
                    name=m["name"], response=json.loads(m["content"])
                )
            )
            continue
        flush()
        if role == "user":
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=m["content"])])
            )
        elif m.get("tool_calls"):
            if m.get("raw") is not None:
                contents.append(m["raw"])
            else:
                parts = [
                    types.Part.from_function_call(name=c["name"], args=c["args"])
                    for c in m["tool_calls"]
                ]
                contents.append(types.Content(role="model", parts=parts))
        else:
            contents.append(
                types.Content(role="model", parts=[types.Part.from_text(text=m["content"])])
            )
    flush()
    return contents