"""Who should take over when the situation must leave the current owner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Escalation:
    target: str
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"target": self.target, "reason": self.reason}


__all__ = ["Escalation"]
