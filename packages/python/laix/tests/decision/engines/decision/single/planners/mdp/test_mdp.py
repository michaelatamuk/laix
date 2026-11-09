"""The finite MDP planner."""

from __future__ import annotations

from laix import (
    PlannerInput,
    MDPPlanner,
    MdpModel,
    MdpTransition,
    action_values,
    plan_actions,
    value_iteration,
)


def _model(horizon: int | None = 2) -> MdpModel:
    return MdpModel(
        states=("s0", "s1", "s2"),
        actions=("go", "stay"),
        transitions=(
            MdpTransition("s0", "go", "s1", 1.0, 1.0),
            MdpTransition("s0", "stay", "s0", 1.0, 0.0),
            MdpTransition("s1", "go", "s2", 1.0, 2.0),
            MdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        start="s0",
        discount=0.9,
        horizon=horizon,
    )


def test_value_iteration_and_action_values() -> None:
    model = _model()
    values = value_iteration(model)

    assert values["s2"] == 0.0
    assert values["s1"] == 2.0
    assert values["s0"] == 2.8
    assert action_values(model, "s0")[0] == ("go", 2.8)


def test_mdp_planner_returns_the_best_action() -> None:
    plan = MDPPlanner(_model()).solve(
        PlannerInput(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            attributes={"state": "s0"},
        )
    )

    assert plan.verb == "act"
    assert plan.action_id == "go"
    assert plan.score == 2.8
    assert plan.alternatives[0]["action_id"] == "stay"


def test_horizon_limits_lookahead() -> None:
    plan = MDPPlanner(_model(horizon=1)).solve(
        PlannerInput(subject="choose", at="2026-11-01T10:00:00+00:00")
    )

    assert plan.action_id == "go"
    assert plan.score == 1.0


def test_greedy_plan_follows_the_value() -> None:
    assert plan_actions(_model()) == ("s0:go", "s1:go")


def test_transition_probabilities_must_sum_to_one() -> None:
    try:
        MdpModel(
            states=("s0", "s1"),
            actions=("go",),
            transitions=(
                MdpTransition("s0", "go", "s0", 0.4, 0.0),
                MdpTransition("s0", "go", "s1", 0.4, 0.0),
            ),
            start="s0",
        )
    except ValueError as exc:
        assert "sum to" in str(exc)
    else:
        raise AssertionError("expected ValueError")
