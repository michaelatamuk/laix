"""Learn transitions and rewards from observed outcomes, with rollback.

The model is a count table, not a neural network. It is enough to learn a small
domain model from execution outcomes, and it keeps a best snapshot so a host can
reject a learned model that performs worse on a validation set.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

Transition = tuple[str, str, str, float]


@dataclass(frozen=True, slots=True)
class LearnedTransition:
    """The learned distribution for one state and action."""

    state: str
    action: str
    probabilities: dict[str, float]
    expected_reward: float
    count: int


class ModelLearner:
    """A count-based transition and reward model."""

    def __init__(self, *, prior: float = 0.5) -> None:
        if prior < 0:
            raise ValueError("prior must not be negative")
        self.prior = float(prior)
        self._counts: dict[tuple[str, str, str], int] = {}
        self._rewards: dict[tuple[str, str], float] = {}
        self._totals: dict[tuple[str, str], int] = {}
        self._best_score: float | None = None
        self._best: dict[str, Any] | None = None
        self.history: list[tuple[float, bool]] = []

    def observe(
        self,
        state: str,
        action: str,
        next_state: str,
        reward: float,
    ) -> None:
        """Record one transition and its reward."""
        key = (state, action, next_state)
        self._counts[key] = self._counts.get(key, 0) + 1
        pair = (state, action)
        self._rewards[pair] = self._rewards.get(pair, 0.0) + float(reward)
        self._totals[pair] = self._totals.get(pair, 0) + 1

    def transition_probabilities(
        self,
        state: str,
        action: str,
    ) -> dict[str, float]:
        """Return the smoothed distribution over next states."""
        pair = (state, action)
        total = self._totals.get(pair, 0)
        outcomes = {
            next_state: count
            for (item_state, item_action, next_state), count in self._counts.items()
            if item_state == state and item_action == action
        }
        denominator = total + self.prior * max(1, len(outcomes))
        if denominator <= 0:
            return {}
        return {
            next_state: round((count + self.prior) / denominator, 6)
            for next_state, count in sorted(outcomes.items())
        }

    def expected_reward(self, state: str, action: str) -> float:
        """Return the mean observed reward for one state and action."""
        pair = (state, action)
        total = self._totals.get(pair, 0)
        if not total:
            return 0.0
        return round(self._rewards.get(pair, 0.0) / total, 6)

    def learned(self) -> tuple[LearnedTransition, ...]:
        """Return every learned state/action pair."""
        pairs = sorted(self._totals)
        return tuple(
            LearnedTransition(
                state=state,
                action=action,
                probabilities=self.transition_probabilities(state, action),
                expected_reward=self.expected_reward(state, action),
                count=self._totals[(state, action)],
            )
            for state, action in pairs
        )

    def evaluate(self, validation: Iterable[Transition]) -> float:
        """Score the model on transitions it may not have seen.

        Higher is better. The score combines transition log-likelihood and
        reward error, so a learned model that predicts both the next state and
        the reward is preferred.
        """
        items = list(validation)
        if not items:
            return 0.0
        scores: list[float] = []
        for state, action, next_state, reward in items:
            probabilities = self.transition_probabilities(state, action)
            probability = probabilities.get(next_state, 1e-9)
            reward_error = abs(self.expected_reward(state, action) - float(reward))
            scores.append(math.log(probability) - reward_error)
        return round(sum(scores) / len(scores), 6)

    def commit(self, validation: Iterable[Transition]) -> bool:
        """Keep the current model only if it beats the best one so far."""
        score = self.evaluate(validation)
        if self._best_score is None or score >= self._best_score:
            self._best_score = score
            self._best = self.snapshot()
            self.history.append((score, True))
            return True
        if self._best is not None:
            self._restore_counts(self._best)
        self.history.append((score, False))
        return False

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-friendly copy that can be stored or restored."""
        return {
            "counts": [
                {
                    "state": state,
                    "action": action,
                    "next_state": next_state,
                    "count": count,
                }
                for (state, action, next_state), count in sorted(self._counts.items())
            ],
            "rewards": [
                {"state": state, "action": action, "reward": reward}
                for (state, action), reward in sorted(self._rewards.items())
            ],
            "totals": [
                {"state": state, "action": action, "total": total}
                for (state, action), total in sorted(self._totals.items())
            ],
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Replace the model with a stored snapshot."""
        self._restore_counts(snapshot)

    def _restore_counts(self, snapshot: dict[str, Any]) -> None:
        self._counts = {
            (item["state"], item["action"], item["next_state"]): int(item["count"])
            for item in snapshot.get("counts", [])
        }
        self._rewards = {
            (item["state"], item["action"]): float(item["reward"])
            for item in snapshot.get("rewards", [])
        }
        self._totals = {
            (item["state"], item["action"]): int(item["total"])
            for item in snapshot.get("totals", [])
        }

    @property
    def best_score(self) -> float | None:
        return self._best_score


__all__ = ["LearnedTransition", "ModelLearner"]
