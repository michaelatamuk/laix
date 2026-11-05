"""Execution sagas: compensate backward on failure."""

from __future__ import annotations

from laix import ActionOption, ExecutionBridge, ExecutionStep, Saga, SagaStep


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


def test_execution_bridge_compensates_completed_steps() -> None:
    bridge = ExecutionBridge(
        handlers={
            "reserve": lambda action, context: {"reserved": action.id},
            "charge": lambda action, context: (_ for _ in ()).throw(RuntimeError("declined")),
        },
        undo_handlers={
            "reserve": lambda action, context: {"released": action.id},
        },
    )
    result = bridge.run_steps(
        [
            ExecutionStep(ActionOption(id="a1", verb="act", name="reserve")),
            ExecutionStep(ActionOption(id="a2", verb="act", name="charge")),
        ],
        actor="checkout",
    )

    assert result.completed == ("reserve",)
    assert result.compensated == ("reserve",)
    assert result.error == "RuntimeError: declined"
    assert [item.status for item in result.receipts] == ["executed", "failed"]
    assert result.receipts[0].detail == {"reserved": "a1"}


def test_execution_bridge_uses_custom_compensation() -> None:
    calls: list[str] = []
    bridge = ExecutionBridge(
        handlers={
            "reserve": lambda action, context: {"reserved": action.id},
            "charge": lambda action, context: (_ for _ in ()).throw(RuntimeError("declined")),
        }
    )
    result = bridge.run_steps(
        [
            ExecutionStep(
                ActionOption(id="a1", verb="act", name="reserve"),
                compensate=lambda receipt: calls.append(receipt.action_name) or {},
            ),
            ExecutionStep(ActionOption(id="a2", verb="act", name="charge")),
        ]
    )

    assert calls == ["reserve"]
    assert result.compensated == ("reserve",)
