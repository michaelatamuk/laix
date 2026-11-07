"""Temporal adapter template.

A real run needs the `temporalio` client and a running Temporal server. The adapter is kept
explicitly unavailable so the comparison never pretends to have measured it.
"""

from __future__ import annotations

from collections.abc import Sequence

from laix import PlannerInput, PlannerResult

from ..result import AdapterResult


class TemporalAdapter:
    """Durable-execution comparison placeholder for Temporal."""

    name = "temporal"
    dependencies = ("temporalio", "Temporal server")

    def available(self) -> bool:
        return False

    def solve(self, problem: PlannerInput) -> PlannerResult:
        raise RuntimeError("Temporal comparison requires a Temporal server")

    def run(self, problems: Sequence[PlannerInput]) -> AdapterResult:
        return AdapterResult(
            name=self.name,
            available=False,
            dependencies=self.dependencies,
            notes=("requires temporalio and a Temporal server",),
        )


__all__ = ["TemporalAdapter"]
