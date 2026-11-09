"""Async execution and saga methods for :class:`ExecutionBridge`."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Iterable

from ...core.domain.decisions import ActionOption, Decision, ExecutionReceipt
from ...core.support.ids import new_execution_receipt_id
from .approval_required import ApprovalRequired
from .execution_saga_result import ExecutionSagaResult
from .execution_step import ExecutionStep
from .execution_types import AsyncHandler
from .retry import RetryPolicy


class AsyncExecutionMixin:
    """Async half of the execution bridge.

    The concrete bridge owns the handler maps, receipts and idempotency index.
    """

    async def execute_async(
        self,
        decision: Decision,
        *,
        action: ActionOption | None,
        actor: str,
        approver: str | None = None,
        context: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        retry: RetryPolicy | None = None,
        timeout_seconds: float | None = None,
    ) -> ExecutionReceipt:
        """Execute an async handler, or a sync handler off the event loop.

        A timeout returns an ``unknown`` receipt: the action may have happened, so
        reconcile it with provider evidence before retrying.
        """
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
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
        async_handler: AsyncHandler | None = self.async_handlers.get(action.name)
        sync_handler = self.handlers.get(action.name)
        if async_handler is None and sync_handler is None:
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
        policy = retry or RetryPolicy()
        detail: dict[str, Any] = {}
        for attempt in range(1, policy.attempts + 1):
            try:
                if async_handler is not None:
                    work = async_handler(action, dict(context or {}))
                else:
                    work = asyncio.to_thread(sync_handler, action, dict(context or {}))
                if timeout_seconds is None:
                    detail = await work or {}
                else:
                    detail = await asyncio.wait_for(work, timeout=timeout_seconds) or {}
                if attempt > 1:
                    detail = {**detail, "attempts": attempt}
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
            except TimeoutError:
                return self._store(
                    ExecutionReceipt(
                        id=new_execution_receipt_id(),
                        decision_id=decision.decision_id,
                        action_name=action.name,
                        status="unknown",
                        actor=actor,
                        detail={
                            "attempts": attempt,
                            "timeout_seconds": timeout_seconds,
                        },
                        error=f"TimeoutError: action did not finish within {timeout_seconds}s",
                        approved_by=approver,
                        idempotency_key=idempotency_key,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - a failed action is data, not a crash
                if attempt < policy.attempts:
                    delay = policy.delay(attempt)
                    if delay:
                        await asyncio.sleep(delay)
                    continue
                return self._store(
                    ExecutionReceipt(
                        id=new_execution_receipt_id(),
                        decision_id=decision.decision_id,
                        action_name=action.name,
                        status="failed",
                        actor=actor,
                        detail={"attempts": attempt},
                        error=f"{type(exc).__name__}: {exc}",
                        approved_by=approver,
                        idempotency_key=idempotency_key,
                    )
                )
        raise RuntimeError("unreachable")

    async def run_steps_async(
        self,
        steps: Iterable[ExecutionStep],
        *,
        actor: str = "system",
        retry: RetryPolicy | None = None,
        timeout_seconds: float | None = None,
    ) -> ExecutionSagaResult:
        """Async variant of ``run_steps`` for async or sync handlers."""
        receipts: list[ExecutionReceipt] = []
        completed: list[tuple[ExecutionStep, ExecutionReceipt]] = []
        compensated: list[str] = []
        failure: list[str] = []

        async def compensate_completed() -> None:
            for done_step, done_receipt in reversed(completed):
                try:
                    did_compensate = False
                    result = None
                    if done_step.compensate is not None:
                        result = done_step.compensate(done_receipt)
                        did_compensate = True
                    elif self.can_undo(done_step.action.name):
                        result = asyncio.to_thread(
                            self.undo,
                            done_receipt.id,
                            actor=done_step.actor or actor,
                        )
                        did_compensate = True
                    if inspect.isawaitable(result):
                        await result
                    if did_compensate:
                        compensated.append(done_step.action.name)
                except Exception:  # noqa: BLE001 - compensation is best effort
                    continue

        for step in steps:
            decision = step.decision or Decision(
                verb=step.action.verb,
                confidence=1.0,
                reason_code="execution_step",
                rationale=step.action.name,
            )
            try:
                receipt = await self.execute_async(
                    decision,
                    action=step.action,
                    actor=step.actor or actor,
                    approver=step.approver,
                    context=step.context,
                    idempotency_key=step.idempotency_key,
                    retry=retry,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:  # noqa: BLE001 - a failed saga is data
                failure.append(f"{type(exc).__name__}: {exc}")
                await compensate_completed()
                break
            receipts.append(receipt)
            if receipt.status in {"executed", "duplicate"}:
                completed.append((step, receipt))
                continue
            failure.append(receipt.error or f"{step.action.name} did not execute")
            await compensate_completed()
            break

        return ExecutionSagaResult(
            completed=tuple(step.action.name for step, _ in completed),
            compensated=tuple(compensated),
            receipts=tuple(receipts),
            error=failure[0] if failure else None,
        )


__all__ = ["AsyncExecutionMixin"]
