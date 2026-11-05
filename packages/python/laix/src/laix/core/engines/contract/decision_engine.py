"""The protocol every external or built-in solver implements."""

from __future__ import annotations

from typing import Protocol

from .decision_problem import DecisionProblem
from .plan import Plan


class DecisionEngine(Protocol):
    """An external or built-in solver behind ``EnginePolicy``."""

    def solve(self, problem: DecisionProblem) -> Plan:
        ...


__all__ = ["DecisionEngine"]
