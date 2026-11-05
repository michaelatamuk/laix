"""Execution sagas: compensate backward on failure."""

from __future__ import annotations

from laix import Saga, SagaStep


def test_saga_compensates_completed_steps_in_reverse() -> None:
    log: list[str] = []

    def first() -> dict:
        log.append("first")
        return {}

    def first_compensate() -> dict:
        log.append("undo first")
        return {}

    def second() -> dict:
        log.append("second")
        raise RuntimeError("boom")

    result = Saga().run(
        [
            SagaStep("first", first, first_compensate),
            SagaStep("second", second),
        ]
    )

    assert result.completed == ("first",)
    assert result.compensated == ("first",)
    assert "RuntimeError: boom" in (result.error or "")
    assert log == ["first", "second", "undo first"]


def test_saga_succeeds_without_compensation() -> None:
    result = Saga().run([SagaStep("first", lambda: {})])

    assert result.completed == ("first",)
    assert result.compensated == ()
    assert result.error is None
