"""Execution-aware planning: the cost of acting changes the choice."""

from __future__ import annotations

import pytest

from laix import (
    ActionOption,
    DecisionProblem,
    ExecutionAwareEngine,
    ExecutionEffect,
    ExecutionWeights,
    UtilityEngine,
)


def _problem(*options: ActionOption) -> DecisionProblem:
    return DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
    )


def test_prefers_a_reversible_option_when_utility_is_equal() -> None:
    plan = ExecutionAwareEngine().solve(
        _problem(
            ActionOption(
                id="reversible",
                verb="act",
                name="reversible",
                expected_benefit=0.7,
            ),
            ActionOption(
                id="irreversible",
                verb="act",
                name="irreversible",
                expected_benefit=0.7,
                reversible=False,
            ),
        )
    )

    assert plan.action_id == "reversible"
    assert plan.reason_code == "execution_aware"


def test_penalizes_an_unknown_outcome() -> None:
    plan = ExecutionAwareEngine().solve(
        _problem(
            ActionOption(id="known", verb="act", name="known", expected_benefit=0.7),
            ActionOption(
                id="unknown",
                verb="act",
                name="unknown",
                expected_benefit=0.8,
                params={"unknown_risk": 0.8},
            ),
        )
    )

    assert plan.action_id == "known"


def test_penalizes_recovery_cost() -> None:
    plan = ExecutionAwareEngine().solve(
        _problem(
            ActionOption(id="cheap", verb="act", name="cheap", expected_benefit=0.7),
            ActionOption(
                id="expensive",
                verb="act",
                name="expensive",
                expected_benefit=0.8,
                params={"execution": {"recovery_cost": 1.0}},
            ),
        )
    )

    assert plan.action_id == "cheap"


def test_penalizes_an_approval_step() -> None:
    plan = ExecutionAwareEngine().solve(
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


def test_matches_the_utility_engine_without_execution_facts() -> None:
    options = (
        ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
        ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
    )
    problem = _problem(*options)

    assert (
        ExecutionAwareEngine().solve(problem).action_id
        == UtilityEngine().solve(problem).action_id
    )


def test_unknown_risk_is_clamped() -> None:
    assert ExecutionEffect(unknown_risk=2.0).unknown_risk == 1.0
    assert ExecutionEffect(unknown_risk=-1.0).unknown_risk == 0.0


def test_negative_weight_is_rejected() -> None:
    with pytest.raises(ValueError):
        ExecutionWeights(recovery=-1.0)
