"""Small transport adapters: feed a session from a queue, iterable, NDJSON or SSE."""

from __future__ import annotations

import asyncio
import json
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


async def from_ndjson(lines: AsyncIterator[str]) -> AsyncIterator[DecisionRequest]:
    """Read one request per JSON line."""
    async for line in lines:
        text = line.strip()
        if text:
            yield DecisionRequest(**json.loads(text))


async def from_sse(lines: AsyncIterator[str]) -> AsyncIterator[DecisionRequest]:
    """Read `data:` frames from a text/event-stream source."""
    data: list[str] = []
    async for line in lines:
        if line.startswith("data:"):
            data.append(line[5:].strip())
        elif not line.strip() and data:
            yield DecisionRequest(**json.loads("\n".join(data)))
            data = []
    if data:
        yield DecisionRequest(**json.loads("\n".join(data)))


__all__ = ["from_ndjson", "from_queue", "from_sse", "from_sync"]
