"""CABB resolves commitments owned by another party."""

from __future__ import annotations

from datetime import timedelta

from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    CommitmentRef,
    DecisionScenario,
    DecisionStep,
)

SUPPLIER = CommitmentRef(owner="supplier", ledger="supplier", id="ship")


def _scenario(source: str, verified_at: str | None = None) -> DecisionScenario:
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
                        params={
                            "commitments": {
                                "fulfills": ["c1"],
                                "hard": True,
                            }
                        },
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


def test_reported_external_dependency_blocks_the_option() -> None:
    plan = CABBPlanner().plan(_scenario("reported"))

    assert plan.actions == ("wait",)


def test_reported_dependency_can_be_allowed_explicitly() -> None:
    plan = CABBPlanner(require_verified=False).plan(_scenario("reported"))

    assert plan.actions == ("deliver",)


def test_verified_external_dependency_allows_the_option() -> None:
    plan = CABBPlanner().plan(
        _scenario("verified", "2026-11-01T09:30:00+00:00")
    )

    assert plan.actions == ("deliver",)


def test_stale_external_dependency_blocks_the_option() -> None:
    plan = CABBPlanner(max_verification_age=timedelta(hours=1)).plan(
        _scenario("verified", "2026-10-30T09:00:00+00:00")
    )

    assert plan.actions == ("wait",)
