"""Reason about another owner's commitments before acting."""

from __future__ import annotations

from laix import Commitment, CommitmentGraph, CommitmentLedger, CommitmentRef

local = CommitmentLedger(
    (
        Commitment(
            id="deliver",
            subject="deliver to the customer",
            external_depends_on=(
                CommitmentRef(owner="supplier", ledger="supplier", id="ship"),
            ),
        ),
    )
)
reported = Commitment(
    id="ship",
    subject="ship the part",
    owner="supplier",
    ledger="supplier",
    status="done",
    source="reported",
)
graph = CommitmentGraph(local, (reported,))

blocker = graph.blockers(local.get("deliver"), require_verified=True)[0]
print(blocker.reason, blocker.ref.owner, blocker.ref.id)
