from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ..approval import ApprovalPolicy
from ..audit import AuditSink
from ..safety import RiskTier, classify_command
from .registry import ToolRegistry, ToolSpec

DEFAULT_TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 8000


def register_shell_tools(
    registry: ToolRegistry,
    workspace: Path,
    audit_sink: AuditSink,
    approval_policy: ApprovalPolicy | None = None,
) -> None:
    def run_command(
        command: str,
        cwd: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        plan_only: bool = False,
    ) -> str:
        workdir = workspace.resolve()
        if cwd:
            workdir = (workdir / cwd).resolve()
            try:
                workdir.relative_to(workspace.resolve())
            except ValueError:
                return f"ERROR: cwd escapes workspace: {cwd}"
        if not workdir.exists():
            return f"ERROR: cwd does not exist: {cwd}"

        decision = classify_command(command)
        details = {"command": command, "cwd": str(workdir), "plan_only": plan_only}

        if plan_only:
            audit_sink.record(
                tool="run_command",
                decision=decision,
                outcome="plan_only",
                workspace=workspace,
                details=details,
            )
            return f"PLAN: {decision.tier.name} {decision.reason}: would run {command}"

        if decision.tier is RiskTier.BLOCKED:
            audit_sink.record(
                tool="run_command",
                decision=decision,
                outcome="refused",
                workspace=workspace,
                details=details,
            )
            return f"REFUSED: blocked command ({decision.reason})"

        if decision.tier.at_least(RiskTier.DANGEROUS):
            if approval_policy is None:
                audit_sink.record(
                    tool="run_command",
                    decision=decision,
                    outcome="no_approver",
                    workspace=workspace,
                    details=details,
                )
                return f"REFUSED: command requires approval ({decision.reason})"
            if not approval_policy.decide(decision, command, str(workdir)):
                audit_sink.record(
                    tool="run_command",
                    decision=decision,
                    outcome="denied",
                    workspace=workspace,
                    details=details,
                )
                return "Command cancelled."

        try:
            completed = subprocess.run(
                command,
                shell=True,
                cwd=str(workdir),
                env={**os.environ, "TERM": "dumb"},
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return f"ERROR: command timed out after {timeout}s"

        output = completed.stdout
        if completed.stderr:
            output += "\n--- stderr ---\n" + completed.stderr
        output = output.strip() or f"(no output, exit code {completed.returncode})"
        if len(output) > MAX_OUTPUT_CHARS:
            output = output[:MAX_OUTPUT_CHARS] + f"\n... [truncated, {len(output)} chars total]"
        if completed.returncode != 0:
            output += f"\n[exit code: {completed.returncode}]"

        audit_sink.record(
            tool="run_command",
            decision=decision,
            outcome="executed",
            workspace=workspace,
            details=details,
        )
        return output

    registry.register(
        ToolSpec(
            name="run_command",
            description="Run a shell command inside the workspace with timeout and safety gates.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "cwd": {"type": ["string", "null"], "default": None},
                    "timeout": {"type": "integer", "default": DEFAULT_TIMEOUT_SECONDS},
                    "plan_only": {"type": "boolean", "default": False},
                },
                "required": ["command"],
            },
            fn=run_command,
        )
    )
