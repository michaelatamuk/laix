"""One planner's answer to one case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LiveBenchRow:
    """One planner's answer to one case."""

    case: str
    tags: tuple[str, ...]
    planner: str
    action_id: str | None
    verb: str
    expected: tuple[str, ...]
    correct: bool | None
    safe: bool
    irreversible: bool
    latency_ms: float
    score: float | None
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case,
            "tags": list(self.tags),
            "planner": self.planner,
            "action_id": self.action_id,
            "verb": self.verb,
            "expected": list(self.expected),
            "correct": self.correct,
            "safe": self.safe,
            "irreversible": self.irreversible,
            "latency_ms": round(self.latency_ms, 4),
            "score": self.score,
            "reason_code": self.reason_code,
        }


__all__ = ["LiveBenchRow"]
