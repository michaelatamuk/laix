"""Human-attention planning: human attention is a budget."""

from __future__ import annotations

import pytest

from laix import (
    ActionOption,
    HumanAttentionPlanner,
    HumanAttentionBudget,
    HumanAttentionWeights,
    PlannerInput,
    UtilityPlanner,
)


def _problem(*options: ActionOption, **attributes: object) -> PlannerInput:
    return PlannerInput(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes=dict(attributes),
    )


def test_low_attention_wins_when_utility_is_close() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.7),
            ActionOption(
                id="guide",
                verb="guide",
                name="guide",
                expected_benefit=0.75,
                interrupt_cost=0.8,
            ),
        )
    )

    assert plan.action_id == "direct"
    assert plan.reason_code == "human_attention_aware"


def test_blocks_a_human_option_when_the_budget_is_gone() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
            human_attention_budget=0.2,
            human_attention_spent=0.2,
        )
    )

    assert plan.action_id == "act"
    assert plan.attributes["human_attention_budget_blocked"] is None


def test_waits_when_every_option_needs_attention() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="guide", verb="guide", name="guide", expected_benefit=0.8),
            human_attention_budget=0.0,
        )
    )

    assert plan.verb == "wait"
    assert plan.reason_code == "human_attention_budget_exhausted"


def test_approval_counts_as_attention() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.7),
            ActionOption(
                id="approval",
                verb="act",
                name="approval",
                expected_benefit=0.75,
                requires_approval=True,
            ),
        )
    )

    assert plan.action_id == "direct"


def test_a_rejected_approval_blocks_the_option() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="rejected", verb="act", name="rejected", expected_benefit=0.9),
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.6),
            approvals={"rejected": "rejected"},
        )
    )

    assert plan.action_id == "direct"


def test_an_approved_option_does_not_pay_the_approval_cost() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.7),
            ActionOption(
                id="approved",
                verb="act",
                name="approved",
                expected_benefit=0.75,
                requires_approval=True,
            ),
            approvals={"approved": "approved"},
        )
    )

    assert plan.action_id == "approved"


def test_a_pending_approval_still_costs_attention() -> None:
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.7),
            ActionOption(
                id="pending",
                verb="act",
                name="pending",
                expected_benefit=0.75,
                requires_approval=True,
            ),
            approvals={"pending": "pending"},
        )
    )

    assert plan.action_id == "direct"


def test_human_attention_budget_object_is_shared() -> None:
    budget = HumanAttentionBudget(total=1.0, spent=0.9)
    plan = HumanAttentionPlanner().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
            human_attention_budget=budget,
        )
    )

    assert plan.action_id == "act"
    assert round(budget.remaining(), 6) == 0.1
    assert budget.spend(0.1) == 0.0


def test_matches_the_utility_planner_without_attention_facts() -> None:
    options = (
        ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
        ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
    )
    problem = _problem(*options)

    assert (
        HumanAttentionPlanner().solve(problem).action_id
        == UtilityPlanner().solve(problem).action_id
    )


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError):
        HumanAttentionWeights(interrupt=-1.0)
