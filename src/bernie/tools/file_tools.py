from __future__ import annotations

from pathlib import Path

from .registry import ToolRegistry, ToolSpec


def resolve_workspace_path(workspace: Path, path: str) -> Path:
    root = workspace.resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {path}") from exc
    return target


def register_file_tools(registry: ToolRegistry, workspace: Path) -> None:
    def read_file(path: str, start_line: int = 1, end_line: int | None = None) -> str:
        try:
            target = resolve_workspace_path(workspace, path)
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        except FileNotFoundError:
            return f"ERROR: file not found: {path}"
        except IsADirectoryError:
            return f"ERROR: path is a directory: {path}"
        except ValueError as exc:
            return f"ERROR: {exc}"

        start = max(start_line, 1)
        stop = len(lines) if end_line is None else min(end_line, len(lines))
        selected = lines[start - 1:stop]
        return "\n".join(f"{idx:4d} | {line}" for idx, line in enumerate(selected, start=start))

    registry.register(
        ToolSpec(
            name="read_file",
            description="Read a UTF-8 text file inside the workspace with optional line bounds.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer", "default": 1},
                    "end_line": {"type": ["integer", "null"], "default": None},
                },
                "required": ["path"],
            },
            fn=read_file,
        )
    )

