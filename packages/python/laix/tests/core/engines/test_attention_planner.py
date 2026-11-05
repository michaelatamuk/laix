"""Attention-aware planning: human attention is a budget."""

from __future__ import annotations

import pytest

from laix import (
    ActionOption,
    AttentionAwareEngine,
    AttentionWeights,
    DecisionProblem,
    UtilityEngine,
)


def _problem(*options: ActionOption, **attributes: object) -> DecisionProblem:
    return DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes=dict(attributes),
    )


def test_low_attention_wins_when_utility_is_close() -> None:
    plan = AttentionAwareEngine().solve(
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
    assert plan.reason_code == "attention_aware"


def test_blocks_a_human_option_when_the_budget_is_gone() -> None:
    plan = AttentionAwareEngine().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
            attention_budget=0.2,
            attention_spent=0.2,
        )
    )

    assert plan.action_id == "act"
    assert plan.attributes["attention_budget_blocked"] is None


def test_waits_when_every_option_needs_attention() -> None:
    plan = AttentionAwareEngine().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="guide", verb="guide", name="guide", expected_benefit=0.8),
            attention_budget=0.0,
        )
    )

    assert plan.verb == "wait"
    assert plan.reason_code == "attention_budget_exhausted"


def test_approval_counts_as_attention() -> None:
    plan = AttentionAwareEngine().solve(
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


def test_matches_the_utility_engine_without_attention_facts() -> None:
    options = (
        ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
        ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
    )
    problem = _problem(*options)

    assert (
        AttentionAwareEngine().solve(problem).action_id
        == UtilityEngine().solve(problem).action_id
    )


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError):
        AttentionWeights(interrupt=-1.0)
