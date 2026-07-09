from __future__ import annotations

from pathlib import Path

from ..approval import ApprovalPolicy
from ..audit import AuditSink
from ..safety import RiskTier, classify_write
from .registry import ToolRegistry, ToolSpec


def resolve_workspace_path(workspace: Path, path: str) -> Path:
    root = workspace.resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {path}") from exc
    return target


def register_file_tools(
    registry: ToolRegistry,
    workspace: Path,
    audit_sink: AuditSink,
    approval_policy: ApprovalPolicy | None = None,
) -> None:
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

    def write_file(
        path: str,
        content: str,
        mode: str = "overwrite",
        plan_only: bool = False,
    ) -> str:
        if mode not in {"overwrite", "append"}:
            return f"ERROR: invalid write mode: {mode}"
        try:
            target = resolve_workspace_path(workspace, path)
        except ValueError as exc:
            return f"ERROR: {exc}"

        existing = ""
        existing_bytes: int | None = None
        if target.exists():
            try:
                existing = target.read_text(encoding="utf-8", errors="replace")
                existing_bytes = len(existing.encode("utf-8"))
            except IsADirectoryError:
                return f"ERROR: path is a directory: {path}"

        final = existing + content if mode == "append" else content
        decision = classify_write(
            target,
            workspace,
            existing_bytes=existing_bytes,
            new_bytes=len(final.encode("utf-8")),
            mode=mode,
        )
        details = {"path": path, "mode": mode, "plan_only": plan_only}

        if plan_only:
            audit_sink.record(
                tool="write_file",
                decision=decision,
                outcome="plan_only",
                workspace=workspace,
                details=details,
            )
            return f"PLAN: {decision.tier.name} {decision.reason}: would write {path}"

        if decision.tier is RiskTier.BLOCKED:
            audit_sink.record(
                tool="write_file",
                decision=decision,
                outcome="refused",
                workspace=workspace,
                details=details,
            )
            return f"REFUSED: blocked write ({decision.reason})"

        if decision.tier.at_least(RiskTier.DANGEROUS):
            if approval_policy is None:
                audit_sink.record(
                    tool="write_file",
                    decision=decision,
                    outcome="no_approver",
                    workspace=workspace,
                    details=details,
                )
                return f"REFUSED: write requires approval ({decision.reason})"
            if not approval_policy.decide(decision, "write_file", path):
                audit_sink.record(
                    tool="write_file",
                    decision=decision,
                    outcome="denied",
                    workspace=workspace,
                    details=details,
                )
                return "Write cancelled."

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(final, encoding="utf-8")
        audit_sink.record(
            tool="write_file",
            decision=decision,
            outcome="executed",
            workspace=workspace,
            details=details,
        )
        return f"OK: wrote {len(content)} chars to {path}"

    registry.register(
        ToolSpec(
            name="write_file",
            description="Write or append UTF-8 text to a file inside the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {"type": "string", "enum": ["overwrite", "append"], "default": "overwrite"},
                    "plan_only": {"type": "boolean", "default": False},
                },
                "required": ["path", "content"],
            },
            fn=write_file,
        )
    )

