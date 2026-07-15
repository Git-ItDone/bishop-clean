from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agent import AgentLoop
from .approval import ApprovalChoice, ApprovalPolicy
from .audit import JsonlAuditSink
from .clients import OllamaChatClient
from .model import ModelClient, ModelClientError
from .tools.default import build_default_registry


@dataclass(frozen=True)
class RuntimeConfig:
    workspace: Path
    model: str = "qwen2.5-coder:1.5b"
    max_turns: int = 40
    confirm_writes: bool = False
    confirm_commands: bool = False
    audit_log: Path | None = None


DEFAULT_SYSTEM_PROMPT = (
    "You are Bishop, a local-first coding agent. "
    "Use tools when they materially help, keep changes scoped to the workspace, "
    "and explain blockers plainly."
)


def _build_approval_policy(config: RuntimeConfig) -> ApprovalPolicy:
    def approve(_decision, action: str, _context: str) -> ApprovalChoice:
        if action in {"write_file", "edit_file"}:
            allowed = config.confirm_writes
        elif action == "run_command":
            allowed = config.confirm_commands
        else:
            allowed = False
        return ApprovalChoice.ALLOW_ONCE if allowed else ApprovalChoice.REJECT_ONCE

    return ApprovalPolicy(approve)


def run_task(
    config: RuntimeConfig,
    task: str | None,
    list_tools: bool = False,
    model_client: ModelClient | None = None,
) -> str:
    audit_log = config.audit_log or config.workspace / ".bishop" / "audit.jsonl"
    registry = build_default_registry(
        workspace=config.workspace,
        audit_sink=JsonlAuditSink(audit_log),
        approval_policy=_build_approval_policy(config),
    )
    if list_tools:
        return "\n".join(registry.names())
    if not task:
        return "No task provided. REPL mode is not implemented in Bishop Clean yet."

    loop = AgentLoop(
        model_client=model_client or OllamaChatClient(model=config.model),
        registry=registry,
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        max_turns=config.max_turns,
    )
    try:
        result = loop.run(task)
    except ModelClientError as exc:
        return f"ERROR: {exc}"
    return format_agent_result(result.final_text, result.tool_names)


def format_agent_result(final_text: str, tool_names: list[str]) -> str:
    if not tool_names:
        return final_text
    tool_summary = ", ".join(tool_names)
    return f"{final_text}\n\nTools used: {tool_summary}"
