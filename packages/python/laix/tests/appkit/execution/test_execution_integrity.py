"""Execution integrity: idempotency, unknown outcomes and reconciliation."""

from __future__ import annotations

import asyncio

from laix import ActionOption, Decision, ExecutionBridge, ExecutionStep, RetryPolicy


def _decision() -> Decision:
    return Decision(
        verb="act",
        confidence=0.9,
        reason_code="test",
        rationale="test",
        decision_id="DEC-1",
        action_id="pay",
    )


def _action() -> ActionOption:
    return ActionOption(id="pay", verb="act", name="pay")


def test_idempotency_key_runs_the_handler_once() -> None:
    calls: list[int] = []
    bridge = ExecutionBridge(handlers={"pay": lambda action, context: calls.append(1) or {"ok": True}})

    first = bridge.execute(_decision(), action=_action(), actor="agent", idempotency_key="K-1")
    second = bridge.execute(_decision(), action=_action(), actor="agent", idempotency_key="K-1")

    assert first.status == "executed"
    assert second.status == "duplicate"
    assert second.detail["original"] == first.id
    assert calls == [1]


def test_unknown_outcome_can_be_reconciled() -> None:
    bridge = ExecutionBridge(handlers={"pay": lambda action, context: {"ok": True}})
    executed = bridge.execute(_decision(), action=_action(), actor="agent", idempotency_key="K-2")

    unknown = bridge.mark_unknown(executed.id, actor="agent", reason="response lost")
    assert unknown.status == "unknown"

    reconciled = bridge.reconcile(
        unknown.id,
        actor="agent",
        status="executed",
        detail={"confirmed": True},
    )
    assert reconciled.status == "executed"
    assert reconciled.detail["confirmed"] is True
    assert reconciled.idempotency_key == "K-2"


def test_retry_policy_retries_until_the_handler_succeeds() -> None:
    calls: list[int] = []

    def handler(action, context):
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("transient")
        return {"ok": True}

    bridge = ExecutionBridge(handlers={"pay": handler})
    receipt = bridge.execute(
        _decision(),
        action=_action(),
        actor="agent",
        retry=RetryPolicy(attempts=3),
    )

    assert receipt.status == "executed"
    assert receipt.detail == {"ok": True, "attempts": 3}
    assert len(calls) == 3


def test_retry_policy_exhausts_attempts() -> None:
    calls: list[int] = []

    def handler(action, context):
        calls.append(1)
        raise RuntimeError("still broken")

    bridge = ExecutionBridge(handlers={"pay": handler})
    receipt = bridge.execute(
        _decision(),
        action=_action(),
        actor="agent",
        retry=RetryPolicy(attempts=2),
    )

    assert receipt.status == "failed"
    assert receipt.detail["attempts"] == 2
    assert "RuntimeError: still broken" in (receipt.error or "")
    assert len(calls) == 2


def test_retry_policy_backoff_is_capped() -> None:
    policy = RetryPolicy(backoff_seconds=1.0, max_backoff_seconds=3.0)
    assert [policy.delay(attempt) for attempt in (1, 2, 3)] == [1.0, 2.0, 3.0]


def test_async_handler_executes() -> None:
    async def handler(action, context):
        await asyncio.sleep(0)
        return {"ok": True}

    bridge = ExecutionBridge(async_handlers={"pay": handler})
    receipt = asyncio.run(
        bridge.execute_async(_decision(), action=_action(), actor="agent")
    )

    assert receipt.status == "executed"
    assert receipt.detail == {"ok": True}


def test_sync_handler_runs_through_execute_async() -> None:
    bridge = ExecutionBridge(handlers={"pay": lambda action, context: {"ok": True}})
    receipt = asyncio.run(
        bridge.execute_async(_decision(), action=_action(), actor="agent")
    )

    assert receipt.status == "executed"
    assert receipt.detail == {"ok": True}


def test_sync_execute_rejects_an_async_only_handler() -> None:
    async def handler(action, context):
        return {"ok": True}

    bridge = ExecutionBridge(async_handlers={"pay": handler})
    receipt = bridge.execute(_decision(), action=_action(), actor="agent")

    assert receipt.status == "failed"
    assert "use execute_async" in (receipt.error or "")


def test_async_timeout_returns_unknown() -> None:
    async def handler(action, context):
        await asyncio.sleep(0.2)
        return {"ok": True}

    bridge = ExecutionBridge(async_handlers={"pay": handler})
    receipt = asyncio.run(
        bridge.execute_async(
            _decision(),
            action=_action(),
            actor="agent",
            timeout_seconds=0.01,
        )
    )

    assert receipt.status == "unknown"
    assert "TimeoutError" in (receipt.error or "")
    assert receipt.detail["timeout_seconds"] == 0.01


def test_async_retry_until_success() -> None:
    calls: list[int] = []

    async def handler(action, context):
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("transient")
        return {"ok": True}

    bridge = ExecutionBridge(async_handlers={"pay": handler})
    receipt = asyncio.run(
        bridge.execute_async(
            _decision(),
            action=_action(),
            actor="agent",
            retry=RetryPolicy(attempts=3),
        )
    )

    assert receipt.status == "executed"
    assert receipt.detail == {"ok": True, "attempts": 3}
    assert len(calls) == 3


def test_async_saga_compensates_completed_steps() -> None:
    compensated: list[str] = []

    async def first(action, context):
        return {"step": 1}

    async def second(action, context):
        raise RuntimeError("boom")

    bridge = ExecutionBridge(async_handlers={"one": first, "two": second})
    result = asyncio.run(
        bridge.run_steps_async(
            (
                ExecutionStep(
                    action=ActionOption(id="1", verb="act", name="one"),
                    compensate=lambda receipt: compensated.append("one"),
                ),
                ExecutionStep(action=ActionOption(id="2", verb="act", name="two")),
            )
        )
    )

    assert result.completed == ("one",)
    assert result.compensated == ("one",)
    assert "RuntimeError: boom" in (result.error or "")
    assert compensated == ["one"]


def test_execution_state_maps_action_name_to_status() -> None:
    bridge = ExecutionBridge(handlers={"pay": lambda action, context: {"ok": True}})
    executed = bridge.execute(_decision(), action=_action(), actor="agent")
    bridge.mark_unknown(executed.id, actor="agent", reason="response lost")

    assert bridge.execution_state() == {"pay": "unknown"}


def test_reconcile_rejects_an_unknown_status() -> None:
    bridge = ExecutionBridge(handlers={"pay": lambda action, context: {"ok": True}})
    executed = bridge.execute(_decision(), action=_action(), actor="agent")

    try:
        bridge.reconcile(executed.id, actor="agent", status="pending")
    except ValueError as exc:
        assert "cannot reconcile" in str(exc)
    else:
        raise AssertionError("expected ValueError")
