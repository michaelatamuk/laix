"""A storage-free decision record: what, why, evidence, approval, audit and undo."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from ...core.contracts import EvidenceRef


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _hash(payload: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Approval:
    required: bool
    state: str = "pending"
    by: str | None = None
    at: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class Undo:
    available: bool = False
    how: str | None = None
    at: str | None = None


@dataclass(frozen=True)
class AuditEvent:
    at: str
    actor: str
    event: str
    detail: str = ""


@dataclass(frozen=True)
class DecisionRecord:
    id: str
    title: str
    summary: str
    decision: dict[str, Any]
    evidence: tuple[EvidenceRef, ...]
    approval: Approval
    status: str
    created_at: str
    updated_at: str
    audit: tuple[AuditEvent, ...]
    undo: Undo
    metadata: dict[str, Any]
    hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": 1,
            "title": self.title,
            "summary": self.summary,
            "decision": dict(self.decision),
            "evidence": [asdict(item) for item in self.evidence],
            "approval": asdict(self.approval),
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "audit": [asdict(item) for item in self.audit],
            "undo": asdict(self.undo),
            "metadata": dict(self.metadata),
            "hash": self.hash,
        }


def _seal(record: DecisionRecord) -> DecisionRecord:
    payload = record.to_dict()
    payload.pop("hash", None)
    return DecisionRecord(**{**record.__dict__, "hash": _hash(payload)})


def _event(record: DecisionRecord, actor: str, event: str, detail: str) -> DecisionRecord:
    at = _now()
    audit = (*record.audit, AuditEvent(at=at, actor=actor, event=event, detail=detail))
    return DecisionRecord(**{**record.__dict__, "audit": audit, "updated_at": at})


def create_record(
    *,
    title: str,
    decision: str,
    evidence: tuple[EvidenceRef, ...],
    confidence: float = 0.8,
    rationale: str = "",
    requires_approval: bool = True,
    metadata: dict[str, Any] | None = None,
    record_id: str | None = None,
    now: str | None = None,
) -> DecisionRecord:
    if not title.strip() or not decision.strip():
        raise ValueError("title and decision are required")
    if not evidence:
        raise ValueError("at least one evidence ref is required")
    moment = now or _now()
    record = DecisionRecord(
        id=record_id or "dr-" + hashlib.sha256(f"{title}|{moment}".encode()).hexdigest()[:12],
        title=title.strip(),
        summary=decision.strip(),
        decision={"text": decision.strip(), "confidence": max(0.0, min(1.0, confidence)), "rationale": rationale},
        evidence=tuple(evidence),
        approval=Approval(required=requires_approval, state="pending" if requires_approval else "approved"),
        status="draft" if requires_approval else "approved",
        created_at=moment,
        updated_at=moment,
        audit=(AuditEvent(at=moment, actor="agent", event="created"),),
        undo=Undo(),
        metadata=dict(metadata or {}),
        hash="",
    )
    return _seal(record)


def approve(record: DecisionRecord, *, by: str, note: str = "") -> DecisionRecord:
    if record.status != "draft":
        raise ValueError(f"cannot approve a {record.status} record")
    next_record = _event(record, by, "approved", note)
    next_record = DecisionRecord(
        **{
            **next_record.__dict__,
            "approval": Approval(required=True, state="approved", by=by, at=next_record.updated_at, note=note),
            "status": "approved",
            "undo": Undo(available=True, how="Undo before execution"),
        }
    )
    return _seal(next_record)


def reject(record: DecisionRecord, *, by: str, note: str = "") -> DecisionRecord:
    if record.status != "draft":
        raise ValueError(f"cannot reject a {record.status} record")
    next_record = _event(record, by, "rejected", note)
    next_record = DecisionRecord(
        **{
            **next_record.__dict__,
            "approval": Approval(required=True, state="rejected", by=by, at=next_record.updated_at, note=note),
            "status": "rejected",
        }
    )
    return _seal(next_record)


def mark_executed(record: DecisionRecord, *, by: str, note: str = "") -> DecisionRecord:
    if record.status != "approved":
        raise ValueError(f"cannot execute a {record.status} record")
    next_record = _event(record, by, "executed", note)
    next_record = DecisionRecord(**{**next_record.__dict__, "status": "executed"})
    return _seal(next_record)


def undo(record: DecisionRecord, *, by: str, note: str = "") -> DecisionRecord:
    if record.status not in {"approved", "executed"} or not record.undo.available:
        raise ValueError("this record is not undoable")
    next_record = _event(record, by, "undone", note)
    next_record = DecisionRecord(
        **{**next_record.__dict__, "status": "undone", "undo": Undo(available=False, how=record.undo.how, at=next_record.updated_at)}
    )
    return _seal(next_record)


def verify(record: DecisionRecord) -> bool:
    payload = record.to_dict()
    payload.pop("hash", None)
    return _hash(payload) == record.hash
