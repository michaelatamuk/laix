"""One decision, its arm and the measured outcome."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CausalObservation:
    """One decision, its arm and the measured outcome."""

    decision_id: str
    arm: str
    outcome: float
    propensity: float | None = None
    context: dict[str, Any] = field(default_factory=dict)


__all__ = ["CausalObservation"]
