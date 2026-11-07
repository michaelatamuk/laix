"""One decision that keeps a promise, avoids an irreversible action and saves attention."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    PlannerInput,
    LiveCompositePlanner,
)

commitments = (
    Commitment(
        id="c1",
        subject="send the report",
        due="2026-11-01T09:00:00+00:00",
    ),
)

plan = LiveCompositePlanner().solve(
    PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="fast",
                verb="act",
                name="fast",
                expected_benefit=1.0,
                reversible=False,
                interrupt_cost=0.6,
                params={"commitments": {"violates": ["c1"]}},
            ),
            ActionOption(
                id="safe",
                verb="act",
                name="safe",
                expected_benefit=0.6,
                params={"commitments": {"fulfills": ["c1"]}},
            ),
        ),
        attributes={"commitments": commitments},
    )
)

print(
    plan.action_id,
    plan.reason_code,
    ",".join(plan.attributes["commitments_fulfilled"]),
)
