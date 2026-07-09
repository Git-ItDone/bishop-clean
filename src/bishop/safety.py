from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RiskTier(Enum):
    SAFE = 0
    CAUTION = 1
    DANGEROUS = 2
    BLOCKED = 3

    def at_least(self, other: "RiskTier") -> bool:
        return self.value >= other.value


@dataclass(frozen=True)
class SafetyDecision:
    tier: RiskTier
    reason: str
    summary: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def requires_approval(self) -> bool:
        return self.tier.at_least(RiskTier.CAUTION)

    @property
    def is_blocked(self) -> bool:
        return self.tier is RiskTier.BLOCKED


BLOCKED_COMMAND_PATTERNS = (
    re.compile(r"\brm\s+(-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|-rf|-fr)\s+/(\s|$)"),
    re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
    re.compile(r"\bdd\b.*\bof=/dev/(disk|sd|nvme|hd|rdisk)"),
    re.compile(r"\bmkfs(\.[a-z0-9]+)?\b"),
)

DANGEROUS_EXECUTABLES = {
    "rm",
    "rmdir",
    "mv",
    "chmod",
    "chown",
    "chgrp",
    "sudo",
    "doas",
    "su",
    "kill",
    "killall",
    "pkill",
    "brew",
    "pip",
    "pip3",
    "npm",
    "yarn",
}

DANGEROUS_GIT_SUBCOMMANDS = {
    "reset",
    "clean",
    "push",
    "rebase",
    "checkout",
    "restore",
}

SHELL_METACHARS = ("&&", "||", ";", "|", ">", ">>", "<", "`", "$(")

SYSTEM_PROTECTED_ROOTS = (
    "/System",
    "/Library",
    "/usr",
    "/bin",
    "/sbin",
    "/etc",
    "/private/etc",
    "/opt",
)

USER_PROTECTED_NAMES = {
    ".ssh",
    ".gnupg",
    ".aws",
    ".docker",
    ".kube",
    ".netrc",
}


def classify_command(command: str) -> SafetyDecision:
    command = command.strip()
    if not command:
        return SafetyDecision(RiskTier.SAFE, "empty", "(empty command)")

    for pattern in BLOCKED_COMMAND_PATTERNS:
        if pattern.search(command):
            return SafetyDecision(RiskTier.BLOCKED, "blocked-command-pattern", command[:160])

    if re.search(r"\|\s*(sudo\s+)?(sh|bash|zsh)\b", command):
        return SafetyDecision(RiskTier.DANGEROUS, "pipes-into-shell", command[:160])

    first = _first_token(command)
    executable = Path(first).name
    if executable in DANGEROUS_EXECUTABLES:
        return SafetyDecision(RiskTier.DANGEROUS, f"dangerous-executable:{executable}", command[:160])

    if executable == "git":
        subcommand = _nth_token(command, 1)
        if subcommand in DANGEROUS_GIT_SUBCOMMANDS:
            return SafetyDecision(RiskTier.DANGEROUS, f"dangerous-git:{subcommand}", command[:160])
        return SafetyDecision(RiskTier.CAUTION, "git-command", command[:160])

    if any(token in command for token in SHELL_METACHARS):
        return SafetyDecision(RiskTier.CAUTION, "shell-metacharacter", command[:160])

    return SafetyDecision(RiskTier.SAFE, "read-only-or-low-impact", command[:160])


def classify_write(
    target: Path,
    workspace: Path,
    *,
    existing_bytes: int | None,
    new_bytes: int,
    mode: str,
) -> SafetyDecision:
    target = target.expanduser().resolve()
    workspace = workspace.expanduser().resolve()

    protected, reason = is_protected_path(target)
    if protected:
        return SafetyDecision(RiskTier.BLOCKED, reason, f"write {target}")

    if not _is_within(target, workspace):
        return SafetyDecision(RiskTier.DANGEROUS, "outside-workspace", f"write {target}")

    if ".git" in target.relative_to(workspace).parts:
        return SafetyDecision(RiskTier.DANGEROUS, "touches-git-internals", f"write {target}")

    if mode == "overwrite" and existing_bytes and existing_bytes >= 200:
        if new_bytes < existing_bytes * 0.25:
            return SafetyDecision(
                RiskTier.DANGEROUS,
                "large-shrink-overwrite",
                f"write {target}",
                notes=(f"{existing_bytes} bytes -> {new_bytes} bytes",),
            )

    return SafetyDecision(RiskTier.CAUTION, "workspace-write", f"write {target}")


def is_protected_path(path: Path) -> tuple[bool, str]:
    resolved = path.expanduser().resolve()
    if str(resolved) == "/":
        return True, "filesystem-root"

    for root in SYSTEM_PROTECTED_ROOTS:
        root_path = Path(root)
        if root_path.exists() and _is_within(resolved, root_path.resolve()):
            return True, f"system-root:{root}"

    if any(part in USER_PROTECTED_NAMES for part in resolved.parts):
        return True, "user-secret-path"

    return False, ""


def _first_token(command: str) -> str:
    return _nth_token(command, 0)


def _nth_token(command: str, index: int) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    if index >= len(tokens):
        return ""
    return tokens[index]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True

