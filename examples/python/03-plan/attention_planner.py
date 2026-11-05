"""Choose with the human attention budget in the decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    AttentionAwareEngine,
    DecisionProblem,
)

plan = AttentionAwareEngine().solve(
    DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
        ),
        attributes={"attention_budget": 0.2, "attention_spent": 0.2},
    )
)

print(plan.action_id, plan.reason_code, plan.attributes["attention_remaining"])
