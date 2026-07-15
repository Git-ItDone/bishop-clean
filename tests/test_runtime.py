from dataclasses import dataclass

from bishop.model import ModelClientError, ModelMessage, ToolCall
from bishop.runtime import RuntimeConfig, run_task


@dataclass
class ScriptedModel:
    replies: list[ModelMessage]

    def complete(self, messages, tools):
        return self.replies.pop(0)


def test_runtime_config_uses_documented_local_model_default(tmp_path):
    assert RuntimeConfig(workspace=tmp_path).model == "qwen2.5-coder:1.5b"


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


def test_run_task_refuses_command_without_confirmation(tmp_path):
    config = RuntimeConfig(workspace=tmp_path)
    model = ScriptedModel(
        [
            ModelMessage(
                tool_calls=(
                    ToolCall(id="call_1", name="run_command", arguments={"command": "touch blocked.txt"}),
                )
            ),
            ModelMessage(content="command attempted"),
        ]
    )

    run_task(config, task="create a file", model_client=model)

    assert not (tmp_path / "blocked.txt").exists()


def test_run_task_allows_command_with_confirmation(tmp_path):
    config = RuntimeConfig(workspace=tmp_path, confirm_commands=True)
    model = ScriptedModel(
        [
            ModelMessage(
                tool_calls=(
                    ToolCall(id="call_1", name="run_command", arguments={"command": "touch allowed.txt"}),
                )
            ),
            ModelMessage(content="command completed"),
        ]
    )

    result = run_task(config, task="create a file", model_client=model)

    assert result == "command completed\n\nTools used: run_command"
    assert (tmp_path / "allowed.txt").exists()


def test_run_task_refuses_workspace_write_without_confirmation(tmp_path):
    config = RuntimeConfig(workspace=tmp_path)
    model = ScriptedModel(
        [
            ModelMessage(
                tool_calls=(
                    ToolCall(
                        id="call_1",
                        name="write_file",
                        arguments={"path": "note.txt", "content": "hello"},
                    ),
                )
            ),
            ModelMessage(content="write attempted"),
        ]
    )

    run_task(config, task="write a note", model_client=model)

    assert not (tmp_path / "note.txt").exists()


def test_run_task_confirms_workspace_write_and_records_audit(tmp_path):
    config = RuntimeConfig(workspace=tmp_path, confirm_writes=True)
    model = ScriptedModel(
        [
            ModelMessage(
                tool_calls=(
                    ToolCall(
                        id="call_1",
                        name="write_file",
                        arguments={"path": "note.txt", "content": "hello"},
                    ),
                )
            ),
            ModelMessage(content="write completed"),
        ]
    )

    result = run_task(config, task="write a note", model_client=model)

    assert result == "write completed\n\nTools used: write_file"
    assert (tmp_path / "note.txt").read_text(encoding="utf-8") == "hello"
    audit_log = tmp_path / ".bishop" / "audit.jsonl"
    assert '"outcome": "executed"' in audit_log.read_text(encoding="utf-8")
