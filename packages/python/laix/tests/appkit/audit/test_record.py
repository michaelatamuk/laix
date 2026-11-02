"""The decision record lifecycle is storage-free and tamper-evident."""

from __future__ import annotations

from laix import DecisionRecord, approve_record, create_record, reject_record, verify_record
from laix.appkit.audit.decision_record import EvidenceRef, mark_executed, undo


def make() -> DecisionRecord:
    return create_record(
        title="One decision",
        decision="Act now",
        evidence=(EvidenceRef(id="ev-1", quote="The signal is confirmed."),),
        now="2026-11-01T10:00:00+00:00",
        record_id="dr-1",
    )


def test_create_requires_evidence_and_seals() -> None:
    record = make()
    assert record.status == "draft"
    assert record.hash.startswith("sha256:")
    assert verify_record(record)


def test_approve_execute_undo() -> None:
    approved = approve_record(make(), by="owner", note="ok")
    assert approved.status == "approved"
    executed = mark_executed(approved, by="owner")
    assert executed.status == "executed"
    undone = undo(executed, by="owner")
    assert undone.status == "undone"
    assert verify_record(undone)


def test_reject() -> None:
    rejected = reject_record(make(), by="owner", note="no")
    assert rejected.status == "rejected"


def test_tampering_is_detected() -> None:
    record = make()
    tampered = DecisionRecord(**{**record.__dict__, "title": "Changed"})
    assert not verify_record(tampered)
