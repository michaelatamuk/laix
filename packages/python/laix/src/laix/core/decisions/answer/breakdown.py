"""The inspectable score breakdown behind an attention decision."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Breakdown:
    severity: float = 0.0
    due: float = 0.0
    confidence: float = 0.0
    interruption: float = 0.0
    learned: float = 0.0
    total: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "severity": round(self.severity, 2),
            "due": round(self.due, 2),
            "confidence": round(self.confidence, 2),
            "interruption": round(self.interruption, 2),
            "learned": round(self.learned, 2),
            "total": round(self.total, 2),
        }


__all__ = ["Breakdown"]
