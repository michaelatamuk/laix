"""The learned distribution for one state and action."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LearnedTransition:
    """The learned distribution for one state and action."""

    state: str
    action: str
    probabilities: dict[str, float]
    expected_reward: float
    count: int


__all__ = ["LearnedTransition"]
