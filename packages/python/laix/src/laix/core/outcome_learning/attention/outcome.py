"""What happened after an attention decision."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttentionOutcome:
    """What happened after an attention decision. The label the learner needs."""

    signal_id: str
    kind: str
    verb: str
    result: str
    reason_code: str | None = None
    score: float | None = None
    at: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "kind": self.kind,
            "verb": self.verb,
            "result": self.result,
            "reason_code": self.reason_code,
            "score": self.score,
            "at": self.at,
        }


__all__ = ["AttentionOutcome"]
