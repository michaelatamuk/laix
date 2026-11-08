"""Surface a promise, then record and approve it."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import (
    SignalContext,
    DecisionRequest,
    EvidenceRef,
    DecisionClient,
    Signal,
    approve_record,
    create_record,
)

decision = DecisionClient().decide(
    DecisionRequest(
        subject="contract promise",
        at="2026-11-01T10:00:00+00:00",
        signals=(
            Signal(
                id="promise-1",
                kind="promise",
                title="Send the contract by Friday",
                severity="medium",
                confidence=0.85,
                due="2026-11-04T17:00:00+00:00",
                evidence_refs=("quote-17",),
            ),
        ),
        context=SignalContext(
            now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            quiet_hours=None,
            min_severity="medium",
        ),
    )
)[0]

record = approve_record(
    create_record(
        title="Send the contract by Friday",
        decision="Send the contract by Friday.",
        evidence=(EvidenceRef(id="quote-17", quote="I will send it by Friday."),),
    ),
    by="owner",
)

print(decision.verb, decision.reason_code, record.status)
