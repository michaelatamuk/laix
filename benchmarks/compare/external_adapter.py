"""Protocol for one external comparison adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from laix import DecisionProblem, Plan

from .adapter_result import AdapterResult


class ExternalAdapter(Protocol):
    """Run one external orchestration pattern over the shared cases."""

    name: str
    dependencies: tuple[str, ...]

    def available(self) -> bool:
        ...

    def run(self, problems: Sequence[DecisionProblem]) -> AdapterResult:
        ...

    def solve(self, problem: DecisionProblem) -> Plan:
        ...


__all__ = ["ExternalAdapter"]
