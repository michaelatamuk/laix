"""Small transport adapters: feed a session from a queue, iterable, NDJSON or SSE."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterable, AsyncIterator, Callable, Iterable

from ...core.domain.decisions import DecisionRequest
from .dead_letter import DeadLetter

ErrorHandler = Callable[[str, Exception], None]


class DeadLetterQueue:
    """A bounded, callable error sink for NDJSON and SSE sources."""

    def __init__(self, limit: int = 100) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        self.limit = limit
        self._items: list[DeadLetter] = []

    def __call__(self, raw: str, exc: Exception) -> None:
        self.add(raw, exc)

    def add(self, raw: str, exc: Exception) -> None:
        self._items.append(
            DeadLetter(raw=raw, error=f"{type(exc).__name__}: {exc}")
        )
        if len(self._items) > self.limit:
            del self._items[: len(self._items) - self.limit]

    def all(self) -> tuple[DeadLetter, ...]:
        return tuple(self._items)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)


async def _iter_lines(
    lines: AsyncIterable[str] | Iterable[str],
) -> AsyncIterator[str]:
    if hasattr(lines, "__aiter__"):
        async for line in lines:
            yield line
    else:
        for line in lines:
            yield line


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
    lines: AsyncIterable[str] | Iterable[str],
    *,
    on_error: ErrorHandler | None = None,
    strict: bool = True,
) -> AsyncIterator[DecisionRequest]:
    """Read one request per JSON line.

    A malformed line raises by default. Pass ``on_error`` (for example a
    ``DeadLetterQueue``) to collect the bad line, and ``strict=False`` to
    continue with the next line.
    """
    async for line in _iter_lines(lines):
        text = line.strip()
        if not text:
            continue
        request = _request(text, text, on_error=on_error, strict=strict)
        if request is not None:
            yield request


async def from_sse(
    lines: AsyncIterable[str] | Iterable[str],
    *,
    on_error: ErrorHandler | None = None,
    strict: bool = True,
) -> AsyncIterator[DecisionRequest]:
    """Read `data:` frames from a text/event-stream source."""
    data: list[str] = []
    async for line in _iter_lines(lines):
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


__all__ = [
    "DeadLetter",
    "DeadLetterQueue",
    "ErrorHandler",
    "from_ndjson",
    "from_queue",
    "from_sse",
    "from_sync",
]
