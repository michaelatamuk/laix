"""Small execution sagas: run steps, compensate backward on failure."""

from __future__ import annotations

from typing import Iterable

from .saga_result import SagaResult
from .saga_step import SagaStep


class Saga:
    """Run steps in order and compensate the completed ones on failure."""

    def run(self, steps: Iterable[SagaStep]) -> SagaResult:
        completed: list[SagaStep] = []
        try:
            for step in steps:
                step.forward()
                completed.append(step)
        except Exception as exc:  # noqa: BLE001 - a failed saga is data
            compensated: list[str] = []
            for step in reversed(completed):
                if step.compensate is None:
                    continue
                try:
                    step.compensate()
                    compensated.append(step.name)
                except Exception:  # noqa: BLE001 - compensation is best effort
                    continue
            return SagaResult(
                completed=tuple(item.name for item in completed),
                compensated=tuple(compensated),
                error=f"{type(exc).__name__}: {exc}",
            )
        return SagaResult(
            completed=tuple(item.name for item in completed),
            compensated=(),
        )


__all__ = ["Saga", "SagaResult", "SagaStep"]
