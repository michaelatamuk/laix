"""What a ``Planner`` receives to solve one task."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PlannerInput:
    """What a ``Planner`` receives to solve one task."""

    subject: str
    at: str
    situation: Any = None
    options: tuple[Any, ...] = ()
    signals: tuple[Any, ...] = ()
    context: Any = None
    attributes: dict[str, Any] = field(default_factory=dict)


__all__ = ["PlannerInput"]
