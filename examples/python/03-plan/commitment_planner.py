"""Choose an option with the promises already made by the task."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentAwareEngine,
    DecisionProblem,
)

commitments = (
    Commitment(
        id="c1",
        subject="send the report",
        due="2026-11-01T09:00:00+00:00",
    ),
)

plan = CommitmentAwareEngine().solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="send-now",
                verb="act",
                name="send now",
                expected_benefit=1.0,
                params={"commitments": {"violates": ["c1"]}},
            ),
            ActionOption(
                id="send-later",
                verb="act",
                name="send later",
                expected_benefit=0.6,
                params={"commitments": {"fulfills": ["c1"]}},
            ),
        ),
        attributes={"commitments": commitments},
    )
)

print(plan.action_id, plan.reason_code, ",".join(plan.attributes["commitments_fulfilled"]))
