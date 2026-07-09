from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from .safety import RiskTier, SafetyDecision


class ApprovalChoice(Enum):
    ALLOW_ONCE = "allow_once"
    ALLOW_ALWAYS = "allow_always"
    REJECT_ONCE = "reject_once"
    REJECT_ALWAYS = "reject_always"


Approver = Callable[[SafetyDecision, str, str], bool | ApprovalChoice]


@dataclass
class ApprovalMemory:
    allow: dict[RiskTier, set[str]] = field(default_factory=dict)
    reject: dict[RiskTier, set[str]] = field(default_factory=dict)


class ApprovalPolicy:
    def __init__(self, approver: Approver | None = None) -> None:
        self.approver = approver
        self.memory = ApprovalMemory()

    def decide(self, decision: SafetyDecision, action: str, context: str) -> bool:
        cached = self._cached(decision)
        if cached is not None:
            return cached
        if self.approver is None:
            raise RuntimeError("approval required but no approver is configured")
        raw = self.approver(decision, action, context)
        choice = raw if isinstance(raw, ApprovalChoice) else (
            ApprovalChoice.ALLOW_ONCE if raw else ApprovalChoice.REJECT_ONCE
        )
        if choice is ApprovalChoice.ALLOW_ALWAYS:
            self.memory.allow.setdefault(decision.tier, set()).add(decision.reason)
        if choice is ApprovalChoice.REJECT_ALWAYS:
            self.memory.reject.setdefault(decision.tier, set()).add(decision.reason)
        return choice in {ApprovalChoice.ALLOW_ONCE, ApprovalChoice.ALLOW_ALWAYS}

    def _cached(self, decision: SafetyDecision) -> bool | None:
        if decision.reason in self.memory.allow.get(decision.tier, set()):
            return True
        if decision.reason in self.memory.reject.get(decision.tier, set()):
            return False
        return None

