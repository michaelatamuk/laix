"""Retry a transient handler and time out a slow async handler."""

from __future__ import annotations

import asyncio

from laix import ActionOption, Decision, ExecutionBridge, RetryPolicy

decision = Decision(
    verb="act",
    confidence=0.9,
    reason_code="safe_action",
    rationale="close the case",
    decision_id="DEC-1",
    action_id="close",
)
action = ActionOption(id="close", verb="act", name="close case")

calls: list[int] = []


def flaky(action, context):
    calls.append(1)
    if len(calls) < 3:
        raise RuntimeError("transient")
    return {"closed": True}


bridge = ExecutionBridge(handlers={"close case": flaky})
receipt = bridge.execute(
    decision,
    action=action,
    actor="agent",
    retry=RetryPolicy(attempts=3),
)


async def slow(action, context):
    await asyncio.sleep(0.2)
    return {"late": True}


async_bridge = ExecutionBridge(async_handlers={"close case": slow})
timeout = asyncio.run(
    async_bridge.execute_async(
        decision,
        action=action,
        actor="agent",
        timeout_seconds=0.01,
    )
)

print(receipt.status, receipt.detail["attempts"], timeout.status)
