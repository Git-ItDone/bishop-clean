from dataclasses import dataclass

from bishop.model import ModelClientError, ModelMessage, ToolCall
from bishop.runtime import RuntimeConfig, run_task


@dataclass
class ScriptedModel:
    replies: list[ModelMessage]

    def complete(self, messages, tools):
        return self.replies.pop(0)


def test_run_task_lists_tools(tmp_path):
    config = RuntimeConfig(workspace=tmp_path)

    result = run_task(config, task=None, list_tools=True)

    assert "read_file" in result
    assert "run_command" in result


def test_run_task_executes_agent_loop(tmp_path):
    config = RuntimeConfig(workspace=tmp_path)
    model = ScriptedModel([ModelMessage(content="done")])

    result = run_task(config, task="finish", model_client=model)

    assert result == "done"


def test_run_task_executes_tool_calls(tmp_path):
    (tmp_path / "note.txt").write_text("hello\n", encoding="utf-8")
    config = RuntimeConfig(workspace=tmp_path)
    model = ScriptedModel(
        [
            ModelMessage(tool_calls=(ToolCall(id="call_1", name="read_file", arguments={"path": "note.txt"}),)),
            ModelMessage(content="read it"),
        ]
    )

    result = run_task(config, task="read note", model_client=model)

    assert result == "read it\n\nTools used: read_file"


def test_run_task_reports_model_errors(tmp_path):
    class BrokenModel:
        def complete(self, messages, tools):
            raise ModelClientError("offline")

    config = RuntimeConfig(workspace=tmp_path)

    result = run_task(config, task="finish", model_client=BrokenModel())

    assert result == "ERROR: offline"
