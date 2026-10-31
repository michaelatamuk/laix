"""RECALL — a promise from a meeting calls LAIX for timing and a record.

RECALL keeps the capture, transcript and meeting links. It maps a promise to a
Signal, asks LAIX whether to surface it, and records the human approval.

The result is:

    guide worth_surfacing approved

- guide: show the promise to the user.
- worth_surfacing: the rule that says the promise is worth showing.
- approved: the decision record is approved by the owner.
"""

from datetime import datetime, timezone

from laix import (
    Context,
    DecisionRequest,
    Layer,
    Signal,
    approve_record,
    create_record,
)
from laix.record import EvidenceRef

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="RECALL promise",
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
        context=Context(
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
