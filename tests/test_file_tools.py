from pathlib import Path

from bernie.tools.file_tools import resolve_workspace_path
from bernie.tools.default import build_default_registry


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

