from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .safety import SafetyDecision


@dataclass(frozen=True)
class AuditEntry:
    timestamp: str
    tool: str
    tier: str
    outcome: str
    reason: str
    summary: str
    workspace: str
    details: dict[str, Any] = field(default_factory=dict)


class AuditSink:
    def record(
        self,
        *,
        tool: str,
        decision: SafetyDecision,
        outcome: str,
        workspace: Path,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry | None:
        raise NotImplementedError


class NullAuditSink(AuditSink):
    def record(
        self,
        *,
        tool: str,
        decision: SafetyDecision,
        outcome: str,
        workspace: Path,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry | None:
        return None


class JsonlAuditSink(AuditSink):
    def __init__(self, path: Path) -> None:
        self.path = path

    def record(
        self,
        *,
        tool: str,
        decision: SafetyDecision,
        outcome: str,
        workspace: Path,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry | None:
        entry = AuditEntry(
            timestamp=datetime.now().astimezone().isoformat(timespec="seconds"),
            tool=tool,
            tier=decision.tier.name,
            outcome=outcome,
            reason=decision.reason,
            summary=decision.summary,
            workspace=str(workspace),
            details=details or {},
        )
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        except OSError:
            return None
        return entry

