"""What the loop saw for one event and what it skipped."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .detection import Detection


@dataclass(frozen=True, slots=True)
class PerceptionFrame:
    """What the loop saw for one event and what it skipped."""

    subject: str
    at: str
    detections: tuple[Detection, ...]
    allowed: tuple[str, ...]
    skipped: tuple[dict[str, Any], ...]
    uncertainty: float
    deep_calls: int = 0
    cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "at": self.at,
            "detections": [item.to_dict() for item in self.detections],
            "allowed": list(self.allowed),
            "skipped": [dict(item) for item in self.skipped],
            "uncertainty": round(self.uncertainty, 6),
            "deepCalls": self.deep_calls,
            "cost": round(self.cost, 6),
        }


__all__ = ["PerceptionFrame"]
