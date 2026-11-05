"""Learn a transition model from observed outcomes."""

from __future__ import annotations

from laix import ModelLearner

learner = ModelLearner()
learner.observe("s0", "go", "s1", 2.0)
learner.observe("s0", "go", "s1", 2.0)
print(learner.transition_probabilities("s0", "go"), learner.expected_reward("s0", "go"))
