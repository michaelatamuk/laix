"""Aggregate results for one planner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PlannerMetrics:
    """Aggregate results for one planner."""

    planner: str
    decisions: int
    checked: int
    correct: int
    accuracy: float
    safety_violations: int
    irreversible: int
    mean_latency_ms: float
    mean_score: float | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "planner": self.planner,
            "decisions": self.decisions,
            "checked": self.checked,
            "correct": self.correct,
            "accuracy": round(self.accuracy, 4),
            "safety_violations": self.safety_violations,
            "irreversible": self.irreversible,
            "mean_latency_ms": round(self.mean_latency_ms, 4),
            "mean_score": None if self.mean_score is None else round(self.mean_score, 6),
            "reasons": list(self.reasons),
        }


__all__ = ["PlannerMetrics"]
