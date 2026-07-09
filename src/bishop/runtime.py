from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agent import AgentLoop
from .clients import OllamaChatClient
from .model import ModelClient, ModelClientError
from .tools.default import build_default_registry


@dataclass(frozen=True)
class RuntimeConfig:
    workspace: Path
    model: str = "qwen3-coder:30b"
    max_turns: int = 40
    confirm_writes: bool = False
    confirm_commands: bool = False


DEFAULT_SYSTEM_PROMPT = (
    "You are Bishop, a local-first coding agent. "
    "Use tools when they materially help, keep changes scoped to the workspace, "
    "and explain blockers plainly."
)


def run_task(
    config: RuntimeConfig,
    task: str | None,
    list_tools: bool = False,
    model_client: ModelClient | None = None,
) -> str:
    registry = build_default_registry(workspace=config.workspace)
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
