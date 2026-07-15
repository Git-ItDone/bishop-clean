from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


ToolFn = Callable[..., str]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    fn: ToolFn

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def names(self) -> list[str]:
        return list(self._tools)

    def openai_tools(self) -> list[dict[str, Any]]:
        return [tool.as_openai_tool() for tool in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any] | str | None = None) -> str:
        if name not in self._tools:
            return f"ERROR: unknown tool {name!r}. Available: {self.names()}"
        parsed = self._parse_arguments(arguments)
        if not isinstance(parsed, dict):
            return f"ERROR: tool {name!r} expected object arguments."
        tool = self._tools[name]
        try:
            inspect.signature(tool.fn).bind(**parsed)
        except TypeError as exc:
            return f"ERROR: invalid arguments for tool {name!r}: {exc}"
        return tool.fn(**parsed)

    @staticmethod
    def _parse_arguments(arguments: dict[str, Any] | str | None) -> dict[str, Any] | str:
        if arguments is None:
            return {}
        if isinstance(arguments, dict):
            return arguments
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError as exc:
            return f"ERROR: could not parse tool arguments as JSON: {exc}"
        return parsed

