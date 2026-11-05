"""A sanity check between a POMDP belief and its most likely MDP state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlannerComparison:
    """A sanity check between a POMDP belief and its most likely MDP state."""

    pomdp: float
    mdp: float
    gap: float
    state: str


__all__ = ["PlannerComparison"]
