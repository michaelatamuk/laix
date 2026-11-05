"""Run steps and compensate them backward when one fails."""

from __future__ import annotations

from laix import Saga, SagaStep

log: list[str] = []


def first() -> dict:
    log.append("first")
    return {}


def undo_first() -> dict:
    log.append("undo first")
    return {}


def second() -> dict:
    log.append("second")
    raise RuntimeError("boom")


result = Saga().run(
    [
        SagaStep("first", first, undo_first),
        SagaStep("second", second),
    ]
)
print(result.completed, result.compensated, result.error)
