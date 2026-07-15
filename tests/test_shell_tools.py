from pathlib import Path

from bishop.approval import ApprovalPolicy
from bishop.tools.default import build_default_registry


def test_safe_command_requires_explicit_approval(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    result = registry.call("run_command", {"command": "printf hello"})

    assert "requires approval" in result


def test_safe_command_uses_approval(tmp_path: Path):
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)

    result = registry.call("run_command", {"command": "printf hello"})

    assert result == "hello"


def test_run_command_plan_only(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    result = registry.call("run_command", {"command": "rm file.txt", "plan_only": True})

    assert result.startswith("PLAN: DANGEROUS")


def test_dangerous_command_requires_approval(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    result = registry.call("run_command", {"command": "rm file.txt"})

    assert "requires approval" in result


def test_dangerous_command_uses_approval(tmp_path: Path):
    target = tmp_path / "file.txt"
    target.write_text("x", encoding="utf-8")
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)

    result = registry.call("run_command", {"command": "rm file.txt"})

    assert "(no output" in result
    assert not target.exists()
