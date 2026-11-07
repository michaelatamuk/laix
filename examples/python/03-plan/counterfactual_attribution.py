"""CDA: find the smallest counterfactual that would change the decision."""

from __future__ import annotations

from laix import (
    ActionOption,
    CAVODPlanner,
    Commitment,
    DecisionRequest,
    HumanAttentionBudget,
    PlannerPolicy,
    counterfactual_attribution,
    decide,
)

request = DecisionRequest(
    subject="invoice 4832",
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
        ActionOption(
            id="wait",
            verb="wait",
            name="wait for the next review",
            expected_benefit=0.2,
        ),
    ),
    attributes={
        "commitments": (
            Commitment(
                id="c1",
                subject="ask the owner before paying",
                due="2026-11-01T09:00:00+00:00",
            ),
        ),
        "human_attention_budget": HumanAttentionBudget(total=2.0, spent=0.5),
        "uncertainty": 0.8,
    },
)

decision = decide(
    request,
    policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"),
)[0]
report = counterfactual_attribution(decision)

print(report.chosen_id, report.minimal.alternative_id, report.minimal.component, report.minimal.delta)
