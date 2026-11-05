"""Small transport adapters: feed a session from a queue, iterable, NDJSON or SSE."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator, Callable, Iterable

from ...core.decisions import DecisionRequest

ErrorHandler = Callable[[str, Exception], None]


def _request(
    payload: str,
    raw: str,
    *,
    on_error: ErrorHandler | None,
    strict: bool,
) -> DecisionRequest | None:
    try:
        return DecisionRequest(**json.loads(payload))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        if on_error is not None:
            on_error(raw, exc)
        if strict:
            raise
        return None


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


async def from_ndjson(
    lines: AsyncIterator[str],
    *,
    on_error: ErrorHandler | None = None,
    strict: bool = True,
) -> AsyncIterator[DecisionRequest]:
    """Read one request per JSON line.

    A malformed line raises by default. Pass ``on_error`` to collect the bad
    line, and ``strict=False`` to continue with the next line.
    """
    async for line in lines:
        text = line.strip()
        if not text:
            continue
        request = _request(text, text, on_error=on_error, strict=strict)
        if request is not None:
            yield request


async def from_sse(
    lines: AsyncIterator[str],
    *,
    on_error: ErrorHandler | None = None,
    strict: bool = True,
) -> AsyncIterator[DecisionRequest]:
    """Read `data:` frames from a text/event-stream source."""
    data: list[str] = []
    async for line in lines:
        if line.startswith("data:"):
            data.append(line[5:].strip())
        elif not line.strip() and data:
            raw = "\n".join(data)
            request = _request(raw, raw, on_error=on_error, strict=strict)
            if request is not None:
                yield request
            data = []
    if data:
        raw = "\n".join(data)
        request = _request(raw, raw, on_error=on_error, strict=strict)
        if request is not None:
            yield request


__all__ = ["ErrorHandler", "from_ndjson", "from_queue", "from_sse", "from_sync"]
