"""Small transport adapters: feed a session from a queue or a sync iterable."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Iterable

from ...core.decisions import DecisionRequest


async def from_queue(
    queue: asyncio.Queue[DecisionRequest | None],
) -> AsyncIterator[DecisionRequest]:
    """Yield requests until the queue sends ``None``."""
    while True:
        event = await queue.get()
        if event is None:
            return
        yield event


async def from_sync(events: Iterable[DecisionRequest]) -> AsyncIterator[DecisionRequest]:
    """Adapt a synchronous iterable to the stream interface."""
    for event in events:
        yield event


__all__ = ["from_queue", "from_sync"]
