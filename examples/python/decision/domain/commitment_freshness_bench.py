"""Check that freshness changes the cross-owner decision."""

from __future__ import annotations

from datetime import timedelta

from laix import (
    ActionOption,
    Commitment,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    PlannerInput,
)

NOW = "2026-11-01T10:00:00+00:00"
SUPPLIER = CommitmentRef(owner="supplier", ledger="supplier", id="ship")


def _local() -> CommitmentLedger:
    return CommitmentLedger(
        (
            Commitment(
                id="deliver",
                subject="deliver to the customer",
                external_depends_on=(SUPPLIER,),
            ),
        )
    )


def _shipment(source: str, verified_at: str | None = None) -> Commitment:
    return Commitment(
        id="ship",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source=source,
        verified_at=verified_at,
    )


def _problem(graph: CommitmentGraph) -> PlannerInput:
    return PlannerInput(
        subject="deliver",
        at=NOW,
        options=(
            ActionOption(
                id="finish",
                verb="act",
                name="finish the delivery",
                expected_benefit=1.0,
                params={"commitments": {"fulfills": ["deliver"], "hard": True}},
            ),
            ActionOption(
                id="wait",
                verb="wait",
                name="wait for verification",
                expected_benefit=0.1,
            ),
        ),
        attributes={"commitment_graph": graph},
    )


def _decide(external: Commitment | None, *, require_verified=True, max_age=None) -> str:
    graph = CommitmentGraph(
        _local(),
        () if external is None else (external,),
    )
    return CommitmentPlanner(
        require_verified=require_verified,
        max_verification_age=(
            timedelta(hours=max_age) if max_age is not None else None
        ),
    ).solve(_problem(graph)).action_id


CASES = (
    ("fresh", _shipment("verified", "2026-11-01T09:30:00+00:00"), 24, "finish"),
    ("stale", _shipment("verified", "2026-10-30T09:00:00+00:00"), 24, "wait"),
    ("reported", _shipment("reported"), 24, "wait"),
    ("missing", None, 24, "wait"),
)
CASES_WITHOUT_VERIFICATION = (
    ("reported-allowed", _shipment("reported"), None, "finish"),
)

passed = 0
total = 0
for name, external, max_age, expected in CASES:
    total += 1
    actual = _decide(external, max_age=max_age)
    passed += int(actual == expected)
    print(name, actual)

for name, external, max_age, expected in CASES_WITHOUT_VERIFICATION:
    total += 1
    actual = _decide(external, require_verified=False, max_age=max_age)
    passed += int(actual == expected)
    print(name, actual)

print(f"{passed}/{total}")
