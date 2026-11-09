"""The utility and execution parts of one option's score."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionScore:
    """The utility and execution parts of one option's score."""

    utility: float
    execution: float
    total: float
    irreversible: bool = False
    unknown_risk: float = 0.0
    recovery_cost: float = 0.0
    requires_approval: bool = False
    receipt_status: str | None = None
    blocked: str | None = None


__all__ = ["ExecutionScore"]
