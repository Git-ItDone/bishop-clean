from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] | str | None


@dataclass(frozen=True)
class ModelMessage:
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class ModelClient(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:
        raise NotImplementedError

