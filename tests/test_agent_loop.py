from dataclasses import dataclass

from bernie.agent import AgentLoop
from bernie.model import ModelMessage, ToolCall
from bernie.tools.registry import ToolRegistry, ToolSpec


@dataclass
class ScriptedModel:
    replies: list[ModelMessage]

    def complete(self, messages, tools):
        return self.replies.pop(0)


def test_agent_loop_returns_final_text_without_tools():
    model = ScriptedModel([ModelMessage(content="done")])
    loop = AgentLoop(
        model_client=model,
        registry=ToolRegistry(),
        system_prompt="You are Bernie.",
    )

    result = loop.run("say done")

    assert result.final_text == "done"
    assert result.turns == 1


def test_agent_loop_dispatches_tool_call_then_finishes():
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo",
            description="Echo text.",
            parameters={"type": "object", "properties": {"text": {"type": "string"}}},
            fn=lambda text: f"echo:{text}",
        )
    )
    model = ScriptedModel(
        [
            ModelMessage(tool_calls=(ToolCall(id="call_1", name="echo", arguments={"text": "hi"}),)),
            ModelMessage(content="saw echo"),
        ]
    )
    loop = AgentLoop(
        model_client=model,
        registry=registry,
        system_prompt="You are Bernie.",
    )

    result = loop.run("use tool")

    assert result.final_text == "saw echo"
    assert result.turns == 2
    assert result.tool_names == ["echo"]


def test_agent_loop_stops_at_max_turns():
    model = ScriptedModel(
        [
            ModelMessage(tool_calls=(ToolCall(id="call_1", name="missing", arguments={}),)),
            ModelMessage(tool_calls=(ToolCall(id="call_2", name="missing", arguments={}),)),
        ]
    )
    loop = AgentLoop(
        model_client=model,
        registry=ToolRegistry(),
        system_prompt="You are Bernie.",
        max_turns=2,
    )

    result = loop.run("loop")

    assert "Reached max turns" in result.final_text
    assert result.tool_names == ["missing", "missing"]

