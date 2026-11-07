"""Protocol for one external comparison adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from laix import PlannerInput, PlannerResult

from .result import AdapterResult


class ExternalAdapter(Protocol):
    """Run one external orchestration pattern over the shared cases."""

    name: str
    dependencies: tuple[str, ...]

    def available(self) -> bool:
        ...

    def run(self, problems: Sequence[PlannerInput]) -> AdapterResult:
        ...

    def solve(self, problem: PlannerInput) -> PlannerResult:
        ...


__all__ = ["ExternalAdapter"]
