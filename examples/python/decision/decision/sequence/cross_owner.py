"""CABB blocks a reported external promise and allows a verified one."""

from __future__ import annotations

from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    CommitmentRef,
    DecisionScenario,
    DecisionStep,
)

SUPPLIER = CommitmentRef(owner="supplier", ledger="supplier", id="ship")


def scenario(source: str, verified_at: str | None = None) -> DecisionScenario:
    return DecisionScenario(
        steps=(
            DecisionStep(
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="deliver",
                        verb="act",
                        name="deliver",
                        expected_benefit=1.0,
                        params={"commitments": {"fulfills": ["c1"], "hard": True}},
                    ),
                    ActionOption(
                        id="wait",
                        verb="wait",
                        name="wait",
                        expected_benefit=0.1,
                    ),
                ),
            ),
        ),
        commitments=(
            Commitment(
                id="c1",
                subject="deliver",
                external_depends_on=(SUPPLIER,),
            ),
            Commitment(
                id="ship",
                subject="ship",
                owner="supplier",
                ledger="supplier",
                status="done",
                source=source,
                verified_at=verified_at,
            ),
        ),
    )


reported = CABBPlanner().plan(scenario("reported")).actions
verified = CABBPlanner().plan(
    scenario("verified", "2026-11-01T09:30:00+00:00")
).actions

print(",".join(reported), ",".join(verified))
