"""Choose with the human attention budget in the decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    PlannerInput,
    HumanAttentionPlanner,
)

plan = HumanAttentionPlanner().solve(
    PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
        ),
        attributes={"human_attention_budget": 0.2, "human_attention_spent": 0.2},
    )
)

print(plan.action_id, plan.reason_code, plan.attributes["human_attention_remaining"])
