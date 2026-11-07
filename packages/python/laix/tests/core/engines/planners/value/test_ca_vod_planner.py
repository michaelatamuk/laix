from __future__ import annotations

from laix import (
    ActionOption,
    CAVODPlanner,
    Commitment,
    HumanAttentionBudget,
    PlannerInput,
)


def _problem() -> PlannerInput:
    return PlannerInput(
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
                name="wait",
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


def test_ca_vod_adds_information_value_and_chooses_ask() -> None:
    plan = CAVODPlanner().solve(_problem())

    assert plan.verb == "ask"
    assert plan.action_id == "ask"
    assert plan.reason_code == "value_of_decision"
    assert plan.attributes["algorithm"] == "ca_vod.v1"
    assert plan.attributes["information_value"] > 0
    assert plan.attributes["uncertainty"] == 0.8
    assert plan.alternatives


def test_ca_vod_wait_when_there_are_no_options() -> None:
    plan = CAVODPlanner().solve(
        PlannerInput(
            subject="empty",
            at="2026-11-01T10:00:00+00:00",
            options=(),
            attributes={},
        )
    )

    assert plan.verb == "wait"
    assert plan.reason_code == "no_options"
