import json
from pathlib import Path

from bishop.approval import ApprovalPolicy
from bishop.audit import JsonlAuditSink
from bishop.tools.default import build_default_registry


def test_safe_command_requires_explicit_approval(tmp_path: Path):
    registry = build_default_registry(tmp_path)
    result = registry.call("run_command", {"command": "printf hello"})
    assert "requires approval" in result


def test_safe_command_uses_approval(tmp_path: Path):
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)
    assert registry.call("run_command", {"command": "printf hello"}) == "hello"


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


def test_timed_out_command_is_audited(tmp_path: Path):
    audit_path = tmp_path / ".bishop" / "audit.jsonl"
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, audit_sink=JsonlAuditSink(audit_path), approval_policy=policy)
    result = registry.call("run_command", {"command": "sleep 1", "timeout": 0})
    assert result == "ERROR: command timed out after 0s"
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["outcome"] == "timed_out"
    assert record["details"]["command"] == "sleep 1"


def test_escaped_cwd_is_audited(tmp_path: Path):
    audit_path = tmp_path / ".bishop" / "audit.jsonl"
    registry = build_default_registry(tmp_path, audit_sink=JsonlAuditSink(audit_path))
    result = registry.call("run_command", {"command": "printf hello", "cwd": "../outside"})
    assert result == "ERROR: cwd escapes workspace: ../outside"
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    assert record["outcome"] == "invalid_cwd"
