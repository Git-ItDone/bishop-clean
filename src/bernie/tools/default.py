from __future__ import annotations

from pathlib import Path

from .file_tools import register_file_tools
from .registry import ToolRegistry


def build_default_registry(workspace: Path) -> ToolRegistry:
    registry = ToolRegistry()
    register_file_tools(registry=registry, workspace=workspace)
    return registry

