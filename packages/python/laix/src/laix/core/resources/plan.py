"""What the resource scheduler admitted and what it skipped."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResourcePlan:
    allowed: tuple[str, ...]
    skipped: tuple[dict[str, Any], ...]
    deep_calls: int
    cost: float
    reason: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": list(self.allowed),
            "skipped": [dict(item) for item in self.skipped],
            "deepCalls": self.deep_calls,
            "cost": round(self.cost, 6),
            "reason": self.reason,
            "attributes": dict(self.attributes),
        }


__all__ = ["ResourcePlan"]
