"""Execution integrity: idempotency, unknown outcomes and reconciliation."""

from __future__ import annotations

from laix import ActionOption, Decision, ExecutionBridge


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
