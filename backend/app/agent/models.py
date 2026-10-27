from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    """The model asking us to run a tool."""

    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderReply:
    """What an LLM provider returns: text, or tool calls, or both."""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None  # provider data to send back unchanged (e.g. Gemini thought signatures)


@dataclass
class Tool:
    """A function the model may call. `parameters` is a JSON schema."""

    name: str
    description: str
    parameters: dict[str, Any]
    fn: Callable[..., Any]


class LLMProvider(Protocol):
    """Anything with this method can be a provider (Gemini, Claude, a fake)."""

    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[Tool],
    ) -> ProviderReply: ...