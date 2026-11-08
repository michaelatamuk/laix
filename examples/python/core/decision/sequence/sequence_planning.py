"""Finite-horizon sequence planning: exact, rollout and replan."""

from __future__ import annotations

from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    DecisionScenario,
    DecisionStep,
    HumanAttentionBudget,
    ReplanPlanner,
    RolloutPlanner,
)


def scenario() -> DecisionScenario:
    return DecisionScenario(
        steps=(
            DecisionStep(
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="pay",
                        verb="act",
                        name="pay the invoice",
                        expected_benefit=0.95,
                        risk=0.05,
                        requires_approval=True,
                        reversible=False,
                        interrupt_cost=0.6,
                        params={"commitments": {"violates": ["c1"]}},
                    ),
                    ActionOption(
                        id="ask",
                        verb="ask",
                        name="ask the owner",
                        expected_benefit=0.6,
                        interrupt_cost=0.2,
                        params={"commitments": {"fulfills": ["c1"]}},
                    ),
                ),
            ),
            DecisionStep(
                at="2026-11-01T11:00:00+00:00",
                options=(
                    ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.2),
                    ActionOption(id="verify", verb="verify", name="verify", expected_benefit=0.4),
                ),
            ),
        ),
        commitments=(
            Commitment(
                id="c1",
                subject="ask the owner before paying",
                due="2026-11-01T09:00:00+00:00",
            ),
        ),
        human_attention_budget=HumanAttentionBudget(total=2.0, spent=0.5),
    )


exact = CABBPlanner().plan(scenario())
rollout = RolloutPlanner().plan(scenario())
repair = ReplanPlanner().replan(scenario(), ("ask",))

print(
    ",".join(exact.actions),
    exact.score,
    exact.optimal,
    ",".join(rollout.actions),
    ",".join(repair.actions),
)
