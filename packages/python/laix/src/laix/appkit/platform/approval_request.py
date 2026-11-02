"""The approval a platform is asked to obtain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    decision_id: str
    action_name: str
    rationale: str = ""
    risk: float = 0.0
    reversible: bool = True
    evidence: tuple[str, ...] = ()


__all__ = ["ApprovalRequest"]
