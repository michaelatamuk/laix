"""Exact sequence planning beats greedy rollout on an attention tradeoff."""

from __future__ import annotations

from laix import (
    ActionOption,
    CABBPlanner,
    DecisionScenario,
    DecisionStep,
    HumanAttentionBudget,
    RolloutPlanner,
)

scenario = DecisionScenario(
    steps=(
        DecisionStep(
            at="2026-11-01T10:00:00+00:00",
            options=(ActionOption(id="start", verb="wait", name="start", expected_benefit=0.0),),
        ),
        DecisionStep(
            at="2026-11-01T10:10:00+00:00",
            options=(
                ActionOption(id="big", verb="act", name="big", expected_benefit=1.0, interrupt_cost=0.9),
                ActionOption(id="small", verb="act", name="small", expected_benefit=0.6, interrupt_cost=0.3),
            ),
        ),
        DecisionStep(
            at="2026-11-01T10:20:00+00:00",
            options=(
                ActionOption(id="bonus", verb="act", name="bonus", expected_benefit=1.0, interrupt_cost=0.6),
                ActionOption(id="nothing", verb="wait", name="nothing", expected_benefit=0.1),
            ),
        ),
    ),
    human_attention_budget=HumanAttentionBudget(total=1.0, spent=0.0),
)

exact = CABBPlanner().plan(scenario)
greedy = RolloutPlanner().plan(scenario)

print("cabb", ",".join(exact.actions), exact.score)
print("rollout", ",".join(greedy.actions), greedy.score)
