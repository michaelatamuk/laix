"""A snapshot of what is happening, toward which goals, under which limits."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...support.serialize import to_primitive
from ...support.values import clamp
from ...support.version import SCHEMA_VERSION
from .belief import Belief
from .constraint import Constraint
from .goal import Goal
from .observation import Observation

PHASES: tuple[str, ...] = ("observe", "understand", "decide", "act", "verify", "adapt")

HORIZONS: tuple[str, ...] = ("seconds", "minutes", "hours", "days", "weeks")


@dataclass(frozen=True, slots=True)
class Situation:
    """A snapshot of what is happening, toward which goals, under which limits."""

    id: str
    at: str
    subject: str
    observations: tuple[Observation, ...] = ()
    beliefs: tuple[Belief, ...] = ()
    goals: tuple[Goal, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    phase: str = "observe"
    horizon: str = "minutes"
    attributes: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.phase not in PHASES:
            raise ValueError(f"unknown phase: {self.phase}")
        if self.horizon not in HORIZONS:
            raise ValueError(f"unknown horizon: {self.horizon}")

    def belief(self, belief_id: str) -> Belief | None:
        return next((item for item in self.beliefs if item.id == belief_id), None)

    def constraint(self, kind: str) -> Constraint | None:
        return next((item for item in self.constraints if item.kind == kind), None)

    def confidence(self) -> float:
        if self.beliefs:
            return clamp(min(item.confidence for item in self.beliefs))
        try:
            return clamp(float(self.attributes.get("confidence", 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def uncertainty(self) -> float:
        try:
            return clamp(float(self.attributes.get("uncertainty", 1.0 - self.confidence())))
        except (TypeError, ValueError):
            return 1.0 - self.confidence()

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["HORIZONS", "PHASES", "Situation"]
