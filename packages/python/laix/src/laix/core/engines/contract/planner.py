"""The protocol every external or built-in solver implements."""

from __future__ import annotations

from typing import Protocol

from .planner_input import PlannerInput
from .planner_result import PlannerResult


class Planner(Protocol):
    """An external or built-in solver behind ``PlannerPolicy``."""

    def solve(self, problem: PlannerInput) -> PlannerResult:
        ...


__all__ = ["Planner"]
