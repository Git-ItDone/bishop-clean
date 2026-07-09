from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .tools.default import build_default_registry


@dataclass(frozen=True)
class RuntimeConfig:
    workspace: Path
    model: str = "qwen3-coder:30b"
    max_turns: int = 40
    confirm_writes: bool = False
    confirm_commands: bool = False


def run_task(config: RuntimeConfig, task: str | None, list_tools: bool = False) -> str:
    registry = build_default_registry(workspace=config.workspace)
    if list_tools:
        return "\n".join(registry.names())
    if not task:
        return "No task provided. REPL mode is not implemented in Bishop Clean yet."
    return (
        "Bishop Clean runtime skeleton is ready.\n"
        f"Workspace: {config.workspace}\n"
        f"Model: {config.model}\n"
        f"Task: {task}\n"
        "Next step: wire model client and agent loop."
    )

