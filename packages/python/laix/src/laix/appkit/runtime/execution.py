"""Execution bridge: approval, execution, cancellation, recovery and receipts.

LAIX decides; the host executes.  The bridge is a thin, auditable state machine
around named host skills.  It never imports a platform SDK and never performs
domain work itself.

Failure paths that matter (from ``interfaces.md``): the platform refuses, the
action hangs, the situation changes, or a human rejects the request.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from ...core.domain.decisions import ActionOption, Decision, ExecutionReceipt
from ...core.support.ids import new_execution_receipt_id
from ...core.support.verbs import Verb
from .approval_required import ApprovalRequired
from .execution_saga_result import ExecutionSagaResult
from .execution_step import ExecutionStep
from .saga import Saga, SagaStep

Handler = Callable[[ActionOption, dict[str, Any]], dict[str, Any]]


class ExecutionBridge:
    def __init__(self, *, handlers: dict[str, Handler] | None = None, undo_handlers: dict[str, Handler] | None = None) -> None:
        self.handlers: dict[str, Handler] = dict(handlers or {})
        self.undo_handlers: dict[str, Handler] = dict(undo_handlers or {})
        self.receipts: dict[str, ExecutionReceipt] = {}
        self._by_key: dict[str, str] = {}

    def register(self, name: str, handler: Handler, *, undo: Handler | None = None) -> None:
        self.handlers[name] = handler
        if undo is not None:
            self.undo_handlers[name] = undo

    def can_handle(self, name: str) -> bool:
        return name in self.handlers

    def can_undo(self, name: str) -> bool:
        return name in self.undo_handlers

    def execute(
        self,
        decision: Decision,
        *,
        action: ActionOption | None,
        actor: str,
        approver: str | None = None,
        context: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> ExecutionReceipt:
        if idempotency_key and idempotency_key in self._by_key:
            original = self.receipts[self._by_key[idempotency_key]]
            return self._store(
                ExecutionReceipt(
                    id=new_execution_receipt_id(),
                    decision_id=decision.decision_id,
                    action_name=action.name if action else "",
                    status="duplicate",
                    actor=actor,
                    detail={"original": original.id},
                    approved_by=approver,
                    idempotency_key=idempotency_key,
                )
            )
        if action is None:
            return self._store(
                ExecutionReceipt(
                    id=new_execution_receipt_id(),
                    decision_id=decision.decision_id,
                    action_name="",
                    status="refused",
                    actor=actor,
                    error="decision has no action to execute",
                    idempotency_key=idempotency_key,
                )
            )
        if decision.requires_approval and not approver:
            raise ApprovalRequired(f"{action.name} requires human approval")
        if not self.can_handle(action.name):
            return self._store(
                ExecutionReceipt(
                    id=new_execution_receipt_id(),
                    decision_id=decision.decision_id,
                    action_name=action.name,
                    status="failed",
                    actor=actor,
                    error=f"no handler registered for {action.name}",
                    approved_by=approver,
                    idempotency_key=idempotency_key,
                )
            )
        try:
            detail = self.handlers[action.name](action, dict(context or {})) or {}
        except Exception as exc:  # noqa: BLE001 - a failed action is data, not a crash
            return self._store(
                ExecutionReceipt(
                    id=new_execution_receipt_id(),
                    decision_id=decision.decision_id,
                    action_name=action.name,
                    status="failed",
                    actor=actor,
                    error=f"{type(exc).__name__}: {exc}",
                    approved_by=approver,
                    idempotency_key=idempotency_key,
                )
            )
        receipt = self._store(
            ExecutionReceipt(
                id=new_execution_receipt_id(),
                decision_id=decision.decision_id,
                action_name=action.name,
                status="executed",
                actor=actor,
                detail=detail,
                approved_by=approver,
                idempotency_key=idempotency_key,
            )
        )
        if idempotency_key:
            self._by_key[idempotency_key] = receipt.id
        return receipt

    def run_steps(
        self,
        steps: Iterable[ExecutionStep],
        *,
        actor: str = "system",
    ) -> ExecutionSagaResult:
        """Execute steps in order and compensate completed ones on failure."""
        receipts: list[ExecutionReceipt] = []
        completed: dict[str, ExecutionReceipt] = {}
        failure: list[str] = []
        saga_steps: list[SagaStep] = []
        for index, step in enumerate(steps):
            key = str(index)
            decision = step.decision or Decision(
                verb=step.action.verb,
                confidence=1.0,
                reason_code="execution_step",
                rationale=step.action.name,
            )

            def forward(
                step: ExecutionStep = step,
                decision: Decision = decision,
                key: str = key,
            ) -> dict[str, Any]:
                receipt = self.execute(
                    decision,
                    action=step.action,
                    actor=step.actor or actor,
                    approver=step.approver,
                    context=step.context,
                    idempotency_key=step.idempotency_key,
                )
                receipts.append(receipt)
                if receipt.status in {"executed", "duplicate"}:
                    completed[key] = receipt
                    return dict(receipt.detail)
                failure.append(
                    receipt.error or f"{step.action.name} did not execute"
                )
                raise RuntimeError(failure[-1])

            compensate = None
            if step.compensate is not None:

                def compensate(
                    step: ExecutionStep = step,
                    key: str = key,
                ) -> dict[str, Any]:
                    receipt = completed.get(key)
                    if receipt is None:
                        return {}
                    return step.compensate(receipt) or {}

            elif self.can_undo(step.action.name):

                def compensate(key: str = key) -> dict[str, Any]:
                    receipt = completed.get(key)
                    if receipt is None:
                        return {}
                    return dict(self.undo(receipt.id, actor=actor).detail)

            saga_steps.append(SagaStep(step.action.name, forward, compensate))

        result = Saga().run(saga_steps)
        return ExecutionSagaResult(
            completed=result.completed,
            compensated=result.compensated,
            receipts=tuple(receipts),
            error=failure[0] if failure else result.error,
        )

    def refuse(self, decision: Decision, *, action: ActionOption | None, actor: str, reason: str) -> ExecutionReceipt:
        return self._store(
            ExecutionReceipt(
                id=new_execution_receipt_id(),
                decision_id=decision.decision_id,
                action_name=action.name if action else "",
                status="refused",
                actor=actor,
                error=reason,
            )
        )

    def cancel(self, receipt_id: str, *, actor: str, reason: str = "") -> ExecutionReceipt:
        receipt = self.get(receipt_id)
        if receipt.status not in {"pending", "approved"}:
            raise ValueError(f"cannot cancel a receipt that is {receipt.status}")
        cancelled = ExecutionReceipt(
            id=receipt.id,
            decision_id=receipt.decision_id,
            action_name=receipt.action_name,
            status="cancelled",
            actor=actor,
            detail={**receipt.detail, "cancel_reason": reason},
            approved_by=receipt.approved_by,
            idempotency_key=receipt.idempotency_key,
        )
        return self._store(cancelled)

    def undo(self, receipt_id: str, *, actor: str) -> ExecutionReceipt:
        receipt = self.get(receipt_id)
        if receipt.status != "executed":
            raise ValueError(f"cannot undo a receipt that is {receipt.status}")
        handler = self.undo_handlers.get(receipt.action_name)
        if handler is None:
            raise ValueError(f"no undo handler for {receipt.action_name}")
        try:
            detail = handler(ActionOption(id=receipt.id, verb=Verb.ACT, name=receipt.action_name), {"receipt": receipt.to_dict()}) or {}
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"undo failed: {type(exc).__name__}: {exc}") from exc
        undone = ExecutionReceipt(
            id=receipt.id,
            decision_id=receipt.decision_id,
            action_name=receipt.action_name,
            status="undone",
            actor=actor,
            detail={**receipt.detail, "undo": detail},
            previous_state=receipt.detail,
            approved_by=receipt.approved_by,
            idempotency_key=receipt.idempotency_key,
        )
        return self._store(undone)

    def mark_unknown(self, receipt_id: str, *, actor: str, reason: str = "") -> ExecutionReceipt:
        """Record that the action may have happened; do not retry blindly."""
        receipt = self.get(receipt_id)
        unknown = ExecutionReceipt(
            id=receipt.id,
            decision_id=receipt.decision_id,
            action_name=receipt.action_name,
            status="unknown",
            actor=actor,
            detail={**receipt.detail, "unknown_reason": reason},
            approved_by=receipt.approved_by,
            idempotency_key=receipt.idempotency_key,
        )
        return self._store(unknown)

    def reconcile(
        self,
        receipt_id: str,
        *,
        actor: str,
        status: str,
        detail: dict[str, Any] | None = None,
    ) -> ExecutionReceipt:
        """Resolve an unknown outcome with provider evidence."""
        if status not in {"executed", "failed", "unknown"}:
            raise ValueError(f"cannot reconcile to {status}")
        receipt = self.get(receipt_id)
        reconciled = ExecutionReceipt(
            id=receipt.id,
            decision_id=receipt.decision_id,
            action_name=receipt.action_name,
            status=status,
            actor=actor,
            detail={**receipt.detail, **dict(detail or {})},
            approved_by=receipt.approved_by,
            idempotency_key=receipt.idempotency_key,
        )
        if status == "executed" and reconciled.idempotency_key:
            self._by_key[reconciled.idempotency_key] = reconciled.id
        return self._store(reconciled)

    def get(self, receipt_id: str) -> ExecutionReceipt:
        receipt = self.receipts.get(receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        return receipt

    def execution_state(self) -> dict[str, str]:
        """Map action name to its latest receipt status for execution-aware planning."""
        state: dict[str, str] = {}
        for receipt in self.receipts.values():
            state[receipt.action_name] = receipt.status
        return state

    def _store(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        self.receipts[receipt.id] = receipt
        return receipt
