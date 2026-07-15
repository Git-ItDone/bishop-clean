from pathlib import Path

from bishop.approval import ApprovalPolicy
from bishop.tools.file_tools import resolve_workspace_path
from bishop.tools.default import build_default_registry


def test_resolve_workspace_path_blocks_escape(tmp_path: Path):
    try:
        resolve_workspace_path(tmp_path, "../outside.txt")
    except ValueError as exc:
        assert "escapes workspace" in str(exc)
    else:
        raise AssertionError("expected path escape to fail")


def test_read_file_returns_numbered_lines(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("one\ntwo\nthree\n", encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call("read_file", {"path": "notes.txt", "start_line": 2})

    assert "   2 | two" in result
    assert "   3 | three" in result


def test_write_file_inside_workspace(tmp_path: Path):
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)

    result = registry.call("write_file", {"path": "out.txt", "content": "hello"})

    assert result == "OK: wrote 5 chars to out.txt"
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "hello"


def test_write_file_can_plan_without_writing(tmp_path: Path):
    registry = build_default_registry(tmp_path)

    result = registry.call(
        "write_file",
        {"path": "out.txt", "content": "hello", "plan_only": True},
    )

    assert result.startswith("PLAN: CAUTION")
    assert not (tmp_path / "out.txt").exists()


def test_dangerous_write_requires_approval(tmp_path: Path):
    big = tmp_path / "big.txt"
    big.write_text("x" * 1000, encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call("write_file", {"path": "big.txt", "content": "tiny"})

    assert "requires approval" in result


def test_dangerous_write_uses_approval(tmp_path: Path):
    big = tmp_path / "big.txt"
    big.write_text("x" * 1000, encoding="utf-8")
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)

    result = registry.call("write_file", {"path": "big.txt", "content": "tiny"})

    assert result == "OK: wrote 4 chars to big.txt"
    assert big.read_text(encoding="utf-8") == "tiny"


def test_edit_file_replaces_line_range(tmp_path: Path):
    target = tmp_path / "notes.txt"
    target.write_text("one\ntwo\nthree\n", encoding="utf-8")
    policy = ApprovalPolicy(lambda decision, action, context: True)
    registry = build_default_registry(tmp_path, approval_policy=policy)

    result = registry.call(
        "edit_file",
        {
            "path": "notes.txt",
            "start_line": 2,
            "end_line": 2,
            "new_content": "TWO",
        },
    )

    assert result == "OK: edited notes.txt:2-2"
    assert target.read_text(encoding="utf-8") == "one\nTWO\nthree\n"


def test_edit_file_plan_only(tmp_path: Path):
    target = tmp_path / "notes.txt"
    target.write_text("one\ntwo\n", encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call(
        "edit_file",
        {
            "path": "notes.txt",
            "start_line": 1,
            "end_line": 1,
            "new_content": "ONE",
            "plan_only": True,
        },
    )

    assert result.startswith("PLAN: CAUTION")
    assert target.read_text(encoding="utf-8") == "one\ntwo\n"


def test_edit_file_rejects_out_of_bounds_range(tmp_path: Path):
    target = tmp_path / "notes.txt"
    target.write_text("one\n", encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call(
        "edit_file",
        {
            "path": "notes.txt",
            "start_line": 2,
            "end_line": 2,
            "new_content": "nope",
        },
    )

    assert "out of bounds" in result
