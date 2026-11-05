"""A small POMDP: belief update and finite-horizon planning."""

from __future__ import annotations

from laix import (
    DecisionProblem,
    MdpModel,
    MdpTransition,
    ObservationProbability,
    POMDPEngine,
    PomdpModel,
    PomdpTransition,
    belief_entropy,
    belief_from_state,
    belief_update,
    compare_pomdp_to_mdp,
    normalize_belief,
    observation_probability,
    pomdp_value,
    value_iteration,
)


def _model() -> PomdpModel:
    return PomdpModel(
        states=("s0", "s1"),
        actions=("go", "stay"),
        observations=("o0", "o1"),
        transitions=(
            PomdpTransition("s0", "go", "s1", 1.0, 1.0),
            PomdpTransition("s0", "stay", "s0", 1.0, 0.0),
            PomdpTransition("s1", "go", "s1", 1.0, 2.0),
            PomdpTransition("s1", "stay", "s1", 1.0, 0.0),
        ),
        observation_table=(
            ObservationProbability("s0", "go", "o0", 1.0),
            ObservationProbability("s0", "stay", "o0", 1.0),
            ObservationProbability("s1", "go", "o1", 1.0),
            ObservationProbability("s1", "stay", "o1", 1.0),
        ),
        discount=0.9,
        horizon=1,
    )


def test_belief_from_state_and_normalisation() -> None:
    assert belief_from_state("s0", ("s0", "s1")) == {"s0": 1.0, "s1": 0.0}
    assert normalize_belief({"s0": 2.0, "s1": 2.0}, ("s0", "s1")) == {
        "s0": 0.5,
        "s1": 0.5,
    }
    assert belief_entropy({"s0": 0.5, "s1": 0.5}) == 1.0


def test_belief_update_uses_the_observation() -> None:
    belief = belief_from_state("s0", ("s0", "s1"))
    updated = belief_update(_model(), belief, "go", "o1")

    assert updated == {"s1": 1.0}
    assert observation_probability(_model(), belief, "go", "o1") == 1.0


def test_pomdp_value_and_engine() -> None:
    model = _model()
    belief = belief_from_state("s0", ("s0", "s1"))
    assert pomdp_value(model, belief) == 1.0

    plan = POMDPEngine(model).solve(
        DecisionProblem(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            attributes={"belief": belief},
        )
    )

    assert plan.verb == "act"
    assert plan.action_id == "go"
    assert plan.score == 1.0
    assert plan.attributes["entropy"] == 0.0


def test_pomdp_engine_defaults_to_a_uniform_belief() -> None:
    plan = POMDPEngine(_model()).solve(
        DecisionProblem(subject="choose", at="2026-11-01T10:00:00+00:00")
    )

    assert plan.action_id == "go"
    assert plan.attributes["belief"] == {"s0": 0.5, "s1": 0.5}


def test_observation_model_is_required() -> None:
    try:
        PomdpModel(
            states=("s0", "s1"),
            actions=("go",),
            observations=("o0", "o1"),
            transitions=(
                PomdpTransition("s0", "go", "s1", 1.0, 1.0),
            ),
            observation_table=(),
        )
    except ValueError as exc:
        assert "missing observations" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_fully_observable_pomdp_matches_the_mdp_path() -> None:
    pomdp = _model()
    mdp = MdpModel(
        states=pomdp.states,
        actions=pomdp.actions,
        transitions=tuple(
            MdpTransition(
                item.state,
                item.action,
                item.next_state,
                item.probability,
                item.reward,
            )
            for item in pomdp.transitions
        ),
        start="s0",
        discount=pomdp.discount,
        horizon=2,
    )
    belief = belief_from_state("s0", pomdp.states)
    comparison = compare_pomdp_to_mdp(pomdp, mdp, belief, horizon=2)

    assert comparison.state == "s0"
    assert comparison.pomdp == comparison.mdp == value_iteration(mdp)["s0"]
    assert comparison.gap == 0.0
