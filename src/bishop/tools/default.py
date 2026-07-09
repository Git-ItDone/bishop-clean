from __future__ import annotations

from pathlib import Path

from ..approval import ApprovalPolicy
from ..audit import AuditSink, NullAuditSink
from .file_tools import register_file_tools
from .registry import ToolRegistry
from .search_tools import register_search_tools
from .shell_tools import register_shell_tools


def build_default_registry(
    workspace: Path,
    *,
    audit_sink: AuditSink | None = None,
    approval_policy: ApprovalPolicy | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()
    audit_sink = audit_sink or NullAuditSink()
    register_file_tools(
        registry=registry,
        workspace=workspace,
        audit_sink=audit_sink,
        approval_policy=approval_policy,
    )
    register_shell_tools(
        registry=registry,
        workspace=workspace,
        audit_sink=audit_sink,
        approval_policy=approval_policy,
    )
    register_search_tools(registry=registry, workspace=workspace)
    return registry
