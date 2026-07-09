from bishop.tools.default import build_default_registry
from bishop.tools.search_tools import iter_workspace_files


def test_find_files_matches_filename_substring(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "runtime.py").write_text("", encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call("find_files", {"query": "agent"})

    assert result == "src/agent.py"


def test_find_files_refuses_workspace_escape(tmp_path):
    registry = build_default_registry(tmp_path)

    result = registry.call("find_files", {"query": "secret", "path": ".."})

    assert result.startswith("ERROR: path escapes workspace")


def test_search_text_matches_case_insensitive_regex(tmp_path):
    (tmp_path / "README.md").write_text("Bishop is clean\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("nothing\nbishop runs\n", encoding="utf-8")
    registry = build_default_registry(tmp_path)

    result = registry.call("search_text", {"pattern": "bishop"})

    assert result.splitlines() == [
        "README.md:1: Bishop is clean",
        "notes.txt:2: bishop runs",
    ]


def test_search_text_reports_invalid_regex(tmp_path):
    registry = build_default_registry(tmp_path)

    result = registry.call("search_text", {"pattern": "["})

    assert result.startswith("ERROR: invalid regex")


def test_iter_workspace_files_skips_generated_dirs(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("private", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('ok')", encoding="utf-8")

    paths = [path.relative_to(tmp_path).as_posix() for path in iter_workspace_files(tmp_path, tmp_path)]

    assert paths == ["app.py"]
