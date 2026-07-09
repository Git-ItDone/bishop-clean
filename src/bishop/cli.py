from __future__ import annotations

from pathlib import Path

import click

from .runtime import RuntimeConfig, run_task


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("task", required=False)
@click.option(
    "--workspace",
    "-w",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Workspace root for tool execution.",
)
@click.option("--model", default="qwen3-coder:30b", show_default=True)
@click.option("--max-turns", default=40, show_default=True)
@click.option("--confirm-writes", is_flag=True, default=False)
@click.option("--confirm-commands", is_flag=True, default=False)
@click.option("--list-tools", is_flag=True, default=False)
def main(
    task: str | None,
    workspace: Path,
    model: str,
    max_turns: int,
    confirm_writes: bool,
    confirm_commands: bool,
    list_tools: bool,
) -> None:
    """Run Bishop against a concrete local coding task."""
    config = RuntimeConfig(
        workspace=workspace.resolve(),
        model=model,
        max_turns=max_turns,
        confirm_writes=confirm_writes,
        confirm_commands=confirm_commands,
    )
    result = run_task(config=config, task=task, list_tools=list_tools)
    click.echo(result)

