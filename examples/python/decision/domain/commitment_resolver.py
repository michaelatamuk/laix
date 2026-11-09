"""Resolve another owner's commitment and let the planner use it."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    InMemoryCommitmentResolver,
    PlannerInput,
    resolve_commitment_graph,
)

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


def plan(source: str) -> str:
    resolver = InMemoryCommitmentResolver(
        (
            Commitment(
                id="ship",
                subject="ship the part",
                owner="supplier",
                ledger="supplier",
                status="done",
                source=source,
            ),
        )
    )
    graph = resolve_commitment_graph(local, resolver)
    result = CommitmentPlanner().solve(
        PlannerInput(
            subject="deliver",
            at="2026-11-01T10:00:00+00:00",
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
    )
    return result.action_id


print(plan("reported"), plan("verified"))
