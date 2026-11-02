"""The one decision shape returned by every policy and by ``Layer``."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...support.values import clamp
from ...support.verbs import VERBS
from ...support.version import SCHEMA_VERSION
from .breakdown import Breakdown
from .escalation import Escalation
from .evidence_ref import EvidenceRef
from .intent import Intent


@dataclass(frozen=True, slots=True)
class Decision:
    """The one decision shape returned by every policy and by ``Layer``."""

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
    breakdown: Breakdown | None = None
    intent: Intent | None = None
    escalation: Escalation | None = None
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
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.verb not in VERBS:
            raise ValueError(f"unknown verb: {self.verb!r}")
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
        if self.escalation is not None:
            rows.append(
                {
                    "kind": "escalation",
                    "ref": self.escalation.target,
                    "note": self.escalation.reason,
                }
            )
        for item in self.constraints_applied:
            rows.append({"kind": "constraint", "ref": item, "note": ""})
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["Decision"]
