"""Count-based model learning and rollback."""

from __future__ import annotations

import json

from laix import ModelLearner, value_iteration


def test_learner_estimates_transitions_and_reward() -> None:
    learner = ModelLearner(prior=0.5)
    learner.observe("s0", "go", "s1", 1.0)
    learner.observe("s0", "go", "s1", 1.0)
    learner.observe("s0", "go", "s0", 0.0)

    probabilities = learner.transition_probabilities("s0", "go")

    assert probabilities == {"s0": 0.375, "s1": 0.625}
    assert learner.expected_reward("s0", "go") == 0.666667
    assert learner.learned()[0].count == 3


def test_commit_rolls_back_a_worse_model() -> None:
    learner = ModelLearner(prior=0.5)
    learner.observe("s0", "go", "s1", 1.0)
    validation = [("s0", "go", "s1", 1.0)]

    assert learner.commit(validation) is True
    best = learner.best_score

    learner.observe("s0", "go", "s0", -1.0)
    assert learner.commit(validation) is False
    assert learner.best_score == best
    assert learner.transition_probabilities("s0", "go") == {"s1": 1.0}
    assert learner.history[-1][1] is False


def test_snapshot_round_trips() -> None:
    learner = ModelLearner()
    learner.observe("s0", "go", "s1", 2.0)
    snapshot = learner.snapshot()
    assert json.loads(json.dumps(snapshot)) == snapshot

    restored = ModelLearner()
    restored.restore(snapshot)

    assert restored.transition_probabilities("s0", "go") == {"s1": 1.0}
    assert restored.expected_reward("s0", "go") == 2.0


def test_learned_model_feeds_the_mdp_engine() -> None:
    learner = ModelLearner()
    learner.observe("s0", "go", "s1", 1.0)
    learner.observe("s1", "go", "s1", 2.0)
    model = learner.to_mdp_model(start="s0", horizon=2)

    assert value_iteration(model)["s0"] == 2.8
