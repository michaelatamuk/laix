from __future__ import annotations

from laix import (
    ActionOption,
    CAVODPlanner,
    Commitment,
    HumanAttentionBudget,
    ObservationProbability,
    PlannerInput,
    PomdpModel,
    PomdpTransition,
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


def test_ca_vod_uses_belief_state_future_value() -> None:
    model = PomdpModel(
        states=("safe", "risky"),
        actions=("act", "ask", "wait"),
        observations=("ok", "good", "bad"),
        transitions=(
            PomdpTransition(state="safe", action="act", next_state="safe", reward=1.0),
            PomdpTransition(state="risky", action="act", next_state="risky", reward=-1.0),
            PomdpTransition(state="safe", action="ask", next_state="safe"),
            PomdpTransition(state="risky", action="ask", next_state="risky"),
            PomdpTransition(state="safe", action="wait", next_state="safe"),
            PomdpTransition(state="risky", action="wait", next_state="risky"),
        ),
        observation_table=(
            ObservationProbability(next_state="safe", action="act", observation="ok"),
            ObservationProbability(next_state="risky", action="act", observation="ok"),
            ObservationProbability(next_state="safe", action="ask", observation="good"),
            ObservationProbability(next_state="risky", action="ask", observation="bad"),
            ObservationProbability(next_state="safe", action="wait", observation="ok"),
            ObservationProbability(next_state="risky", action="wait", observation="ok"),
        ),
        discount=0.9,
        horizon=2,
    )
    plan = CAVODPlanner(
        pomdp_model=model,
        belief={"safe": 0.5, "risky": 0.5},
    ).solve(
        PlannerInput(
            subject="belief",
            at="2026-11-01T10:00:00+00:00",
            options=(
                ActionOption(id="act", verb="act", name="act", expected_benefit=0.55),
                ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.2),
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
            ),
            attributes={},
        )
    )

    assert plan.action_id == "ask"
    assert plan.attributes["future_value"] > 0
    assert plan.attributes["horizon"] == 2
