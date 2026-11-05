"""One live decision case with the action a careful planner should choose."""

from __future__ import annotations

from dataclasses import dataclass

from .decision_problem import DecisionProblem


@dataclass(frozen=True, slots=True)
class LiveCase:
    """One live decision case with the action a careful planner should choose."""

    name: str
    problem: DecisionProblem
    expected_actions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_actions", tuple(self.expected_actions))
        object.__setattr__(self, "tags", tuple(self.tags))


__all__ = ["LiveCase"]
