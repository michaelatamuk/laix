"""The one decision shape returned by every policy, ``decide`` and ``DecisionClient``."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ....support.values import clamp
from ....support.verbs import VERBS
from ....support.version import SCHEMA_VERSION
from .payload.score_breakdown import ScoreBreakdown
from .payload.evidence_ref import EvidenceRef
from .payload.intent import Intent


DECISION_STATUSES = ("final", "provisional", "superseded")
"""Lifecycle of a decision that belongs to a stream."""

TARGET_MODES = ("one", "some", "all", "peer", "gather")
"""Who receives a decision: one, some, all, a peer or gathered from many."""


@dataclass(frozen=True, slots=True)
class Decision:
    """The one decision shape returned by every policy, ``decide`` and ``DecisionClient``."""

    verb: str
    confidence: float
    reason_code: str
    rationale: str
    decision_id: str = ""
    situation_id: str = ""
    policy_version: str = ""
    action_id: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    requires_approval: bool = False
    score: float | None = None
    breakdown: ScoreBreakdown | None = None
    intent: Intent | None = None
    cost_of_waiting: float = 0.0
    reversible: bool = False
    undo_hint: str | None = None
    trace_id: str = ""
    deliver: bool = True
    record: bool = True
    created_at: str | None = None
    confidence_source: str = ""
    calibrated: bool = False
    alternatives: tuple[dict[str, Any], ...] = ()
    constraints_applied: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    target: str = "one"
    recipients: tuple[str, ...] = ()
    stream_id: str = ""
    event_time: str | None = None
    deadline: str | None = None
    valid_until: str | None = None
    supersedes: str | None = None
    revision: int = 0
    status: str = "final"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.verb not in VERBS:
            raise ValueError(f"unknown verb: {self.verb!r}")
        if self.status not in DECISION_STATUSES:
            raise ValueError(f"unknown decision status: {self.status!r}")
        if self.target not in TARGET_MODES:
            raise ValueError(f"unknown target mode: {self.target!r}")
        object.__setattr__(self, "confidence", clamp(self.confidence))

    def basis(self) -> tuple[dict[str, Any], ...]:
        """A host-neutral basis for a decision record or explain view."""
        rows: list[dict[str, Any]] = [
            {"kind": "reason", "ref": self.reason_code, "note": self.rationale}
        ]
        for item in self.evidence:
            rows.append(
                {
                    "kind": item.kind,
                    "ref": item.id,
                    "note": item.quote or "",
                    "source": item.source or "",
                }
            )
        if self.intent is not None:
            rows.append(
                {
                    "kind": "intent",
                    "ref": self.intent.capability,
                    "note": str(self.intent.args),
                }
            )
        for item in self.constraints_applied:
            rows.append({"kind": "constraint", "ref": item, "note": ""})
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Decision":
        """Rebuild a decision from ``to_dict`` output."""
        known = cls.__dataclass_fields__
        data = {key: value for key, value in payload.items() if key in known}
        data["evidence"] = tuple(
            item if isinstance(item, EvidenceRef) else EvidenceRef(**item)
            for item in data.get("evidence", ())
        )
        intent = data.get("intent")
        if isinstance(intent, dict):
            data["intent"] = Intent(**intent)
        breakdown = data.get("breakdown")
        if isinstance(breakdown, dict):
            data["breakdown"] = ScoreBreakdown(**breakdown)
        data["alternatives"] = tuple(data.get("alternatives", ()))
        data["constraints_applied"] = tuple(data.get("constraints_applied", ()))
        data["recipients"] = tuple(data.get("recipients", ()))
        return cls(**data)


__all__ = ["DECISION_STATUSES", "Decision", "TARGET_MODES"]
