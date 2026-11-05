"""Choose an option with the cost of execution in the decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    DecisionProblem,
    ExecutionAwareEngine,
)

plan = ExecutionAwareEngine().solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="delete-now",
                verb="act",
                name="delete now",
                expected_benefit=0.8,
                reversible=False,
            ),
            ActionOption(
                id="archive",
                verb="act",
                name="archive",
                expected_benefit=0.7,
            ),
        ),
    )
)

print(plan.action_id, plan.reason_code, plan.reversible)
