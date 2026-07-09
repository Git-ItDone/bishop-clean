from __future__ import annotations

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

        return ModelMessage(
            content=message.get("content"),
            tool_calls=tuple(self._parse_tool_call(item) for item in message.get("tool_calls") or ()),
        )

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
