import json
from typing import Any

from app.agent.models import LLMProvider, Tool, ToolCall


def execute_tool(call: ToolCall, tools: dict[str, Tool]) -> dict[str, Any]:
    """Run one tool safely. Failures become data the model can read."""
    tool = tools.get(call.name)
    if tool is None:
        return {"error": f"unknown tool: {call.name}"}
    try:
        return {"result": tool.fn(**call.args)}
    except Exception as exc:  # noqa: BLE001 (a failing tool must never crash the agent)
        # Report only the error type: no internal details leak to the model.
        return {"error": f"tool failed: {type(exc).__name__}"}


def run_turn(
    provider: LLMProvider,
    system_prompt: str,
    history: list[dict[str, Any]],
    user_text: str,
    tools: list[Tool],
    fallback_text: str,
    max_steps: int = 4,
) -> str:
    """Handle one user message. Returns the assistant's final text.

    `fallback_text` is required on purpose: when the model fails, the caller
    must still get a safe message (with emergency numbers from client config).
    """
    history.append({"role": "user", "content": user_text})
    tool_map = {t.name: t for t in tools}

    for _ in range(max_steps):
        reply = provider.generate(system_prompt, history, tools)

        if not reply.tool_calls:
            text = reply.text or fallback_text
            history.append({"role": "assistant", "content": text})
            return text

        history.append(
            {
                "role": "assistant",
                "tool_calls": [{"name": c.name, "args": c.args} for c in reply.tool_calls],
            }
        )
        for call in reply.tool_calls:
            outcome = execute_tool(call, tool_map)
            history.append(
                {
                    "role": "tool",
                    "name": call.name,
                    "content": json.dumps(outcome, ensure_ascii=False, default=str),
                }
            )

    # Too many tool rounds: stop and give the safe message.
    history.append({"role": "assistant", "content": fallback_text})
    return fallback_text