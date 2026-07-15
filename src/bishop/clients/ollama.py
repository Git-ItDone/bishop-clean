from __future__ import annotations

import json
import re
from typing import Any

import httpx

from ..model import ModelClientError, ModelMessage, ToolCall


class OllamaChatClient:
    """OpenAI-compatible chat client for Ollama's local `/v1` API."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str = "http://localhost:11434/v1",
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelMessage:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        try:
            response = self._client.post(f"{self.base_url}/chat/completions", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ModelClientError(f"model request failed: {exc}") from exc

        try:
            data = response.json()
            message = data["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelClientError("model response did not match chat completion schema") from exc

        content = message.get("content")
        tool_calls = tuple(self._parse_tool_call(item) for item in message.get("tool_calls") or ())
        if not tool_calls:
            fallback = self._parse_fallback_tool_call(content)
            if fallback is not None:
                return ModelMessage(content=None, tool_calls=(fallback,))
        return ModelMessage(content=content, tool_calls=tool_calls)

    @staticmethod
    def _parse_fallback_tool_call(content: Any) -> ToolCall | None:
        if not isinstance(content, str):
            return None
        candidate = content.strip()
        fence = re.search(r"```(?:json)?\s*\n?(\{.*?\})\s*```", candidate, flags=re.DOTALL)
        if fence:
            candidate = fence.group(1).strip()
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        name = payload.get("name")
        arguments = payload.get("arguments")
        if not isinstance(name, str) or not name:
            return None
        if not isinstance(arguments, (dict, str)) and arguments is not None:
            return None
        return ToolCall(id=f"fallback_{name}", name=name, arguments=arguments)

    @staticmethod
    def _parse_tool_call(item: dict[str, Any]) -> ToolCall:
        function = item.get("function") or {}
        name = function.get("name")
        if not isinstance(name, str) or not name:
            raise ModelClientError("tool call response is missing function name")
        return ToolCall(
            id=str(item.get("id") or name),
            name=name,
            arguments=function.get("arguments"),
        )
