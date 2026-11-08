"""Restore the best learned model snapshot after a worse observation."""

from __future__ import annotations

from laix import ModelLearner

learner = ModelLearner()
learner.observe("idle", "act", "done", 1.0)
learner.observe("idle", "act", "done", 1.0)

snapshot = learner.snapshot()
learner.observe("idle", "act", "failed", 0.0)
learner.restore(snapshot)

print(learner.transition_probabilities("idle", "act"))
