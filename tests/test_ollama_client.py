import json

import httpx
import pytest

from bishop.clients.ollama import OllamaChatClient
from bishop.model import ModelClientError


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return OllamaChatClient(model="test-model", client=httpx.Client(transport=transport))


def test_ollama_client_posts_chat_completion_payload():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "done",
                        }
                    }
                ]
            },
        )

    client = make_client(handler)

    result = client.complete(
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"type": "function", "function": {"name": "read_file"}}],
    )

    assert seen["url"] == "http://localhost:11434/v1/chat/completions"
    assert seen["payload"]["model"] == "test-model"
    assert seen["payload"]["stream"] is False
    assert seen["payload"]["messages"] == [{"role": "user", "content": "hi"}]
    assert seen["payload"]["tools"][0]["function"]["name"] == "read_file"
    assert result.content == "done"
    assert result.tool_calls == ()


def test_ollama_client_normalizes_tool_calls():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": "{\"path\":\"README.md\"}",
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    client = make_client(handler)

    result = client.complete(messages=[], tools=[])

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "call_1"
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == "{\"path\":\"README.md\"}"


def test_ollama_client_normalizes_fallback_json_tool_call():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": '{"name":"read_file","arguments":{"path":"README.md"}}',
                        }
                    }
                ]
            },
        )

    client = make_client(handler)

    result = client.complete(messages=[], tools=[])

    assert result.content is None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "fallback_read_file"
    assert result.tool_calls[0].name == "read_file"
    assert result.tool_calls[0].arguments == {"path": "README.md"}


def test_ollama_client_normalizes_markdown_fenced_fallback_tool_call():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "```json\n{\"name\":\"read_file\",\"arguments\":{\"path\":\"README.md\"}}\n```",
                        }
                    }
                ]
            },
        )

    client = make_client(handler)

    result = client.complete(messages=[], tools=[])

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "read_file"


def test_ollama_client_normalizes_embedded_fenced_fallback_tool_call():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "I will inspect it first.\n\n```json\n{\"name\":\"read_file\",\"arguments\":{\"path\":\"README.md\"}}\n```\n\nThen I will answer.",
                        }
                    }
                ]
            },
        )

    client = make_client(handler)

    result = client.complete(messages=[], tools=[])

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].arguments == {"path": "README.md"}


def test_ollama_client_rejects_bad_schema():
    def handler(request):
        return httpx.Response(200, json={"not_choices": []})

    client = make_client(handler)

    with pytest.raises(ModelClientError, match="chat completion schema"):
        client.complete(messages=[], tools=[])


def test_ollama_client_wraps_http_errors():
    def handler(request):
        return httpx.Response(500, json={"error": "boom"})

    client = make_client(handler)

    with pytest.raises(ModelClientError, match="model request failed"):
        client.complete(messages=[], tools=[])
