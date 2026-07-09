from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .model import ModelClient
from .tools import ToolRegistry


@dataclass
class AgentResult:
    final_text: str
    turns: int
    tool_names: list[str] = field(default_factory=list)


class AgentLoop:
    def __init__(
        self,
        *,
        model_client: ModelClient,
        registry: ToolRegistry,
        system_prompt: str,
        max_turns: int = 40,
    ) -> None:
        self.model_client = model_client
        self.registry = registry
        self.system_prompt = system_prompt
        self.max_turns = max_turns

    def run(self, task: str) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task},
        ]
        tool_names: list[str] = []

        for turn in range(1, self.max_turns + 1):
            reply = self.model_client.complete(messages, self.registry.openai_tools())
            if reply.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": reply.content,
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.name,
                                    "arguments": call.arguments,
                                },
                            }
                            for call in reply.tool_calls
                        ],
                    }
                )
                for call in reply.tool_calls:
                    tool_names.append(call.name)
                    result = self.registry.call(call.name, call.arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": result,
                        }
                    )
                continue

            return AgentResult(
                final_text=reply.content or "",
                turns=turn,
                tool_names=tool_names,
            )

        return AgentResult(
            final_text=f"Reached max turns ({self.max_turns}) without final response.",
            turns=self.max_turns,
            tool_names=tool_names,
        )

