from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from .file_tools import resolve_workspace_path
from .registry import ToolRegistry, ToolSpec

SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache", ".ruff_cache"}
MAX_FILE_BYTES = 1_000_000


def iter_workspace_files(root: Path, start: Path) -> Iterator[Path]:
    for path in sorted(start.rglob("*")):
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        if path.is_file():
            yield path


def register_search_tools(registry: ToolRegistry, workspace: Path) -> None:
    root = workspace.resolve()

    def find_files(query: str, path: str = ".", max_results: int = 50) -> str:
        if not query:
            return "ERROR: query is required"
        try:
            start = resolve_workspace_path(root, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        if not start.exists():
            return f"ERROR: path does not exist: {path}"
        if start.is_file():
            files = [start]
        else:
            files = list(iter_workspace_files(root, start))

        needle = query.lower()
        matches = [file.relative_to(root).as_posix() for file in files if needle in file.name.lower()]
        matches = matches[: max(max_results, 0)]
        return "\n".join(matches) if matches else "No matching files."

    registry.register(
        ToolSpec(
            name="find_files",
            description="Find files inside the workspace by case-insensitive filename substring.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                    "max_results": {"type": "integer", "default": 50},
                },
                "required": ["query"],
            },
            fn=find_files,
        )
    )

    def search_text(
        pattern: str,
        path: str = ".",
        max_results: int = 50,
        case_sensitive: bool = False,
    ) -> str:
        if not pattern:
            return "ERROR: pattern is required"
        try:
            start = resolve_workspace_path(root, path)
        except ValueError as exc:
            return f"ERROR: {exc}"
        if not start.exists():
            return f"ERROR: path does not exist: {path}"

        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            regex = re.compile(pattern, flags)
        except re.error as exc:
            return f"ERROR: invalid regex: {exc}"

        files = [start] if start.is_file() else iter_workspace_files(root, start)
        results: list[str] = []
        for file in files:
            if len(results) >= max_results:
                break
            try:
                if file.stat().st_size > MAX_FILE_BYTES:
                    continue
                lines = file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for line_number, line in enumerate(lines, start=1):
                if regex.search(line):
                    relative = file.relative_to(root).as_posix()
                    results.append(f"{relative}:{line_number}: {line}")
                    if len(results) >= max_results:
                        break
        return "\n".join(results) if results else "No matches."

    registry.register(
        ToolSpec(
            name="search_text",
            description="Search UTF-8 text files inside the workspace with a regular expression.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "default": "."},
                    "max_results": {"type": "integer", "default": 50},
                    "case_sensitive": {"type": "boolean", "default": False},
                },
                "required": ["pattern"],
            },
            fn=search_text,
        )
    )
