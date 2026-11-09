"""Async feed and async-iterator methods for :class:`StreamSession`."""

from __future__ import annotations

import asyncio
import contextlib
from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, Sequence

from ...core.domain.decisions import Decision, DecisionRequest
from .window import TumblingWindow, WindowBatch

Refiner = Callable[[DecisionRequest], Awaitable[Sequence[Decision]]]


class FeedMixin:
    """Async feeding and backpressure half of the stream session."""

    async def observe_refined(
        self,
        request: DecisionRequest,
        refine: Refiner,
        *,
        status: str = "provisional",
        timeout_ms: int | None = None,
    ) -> list[Decision]:
        """Emit a fast decision, await the deep path, then emit its revision."""
        if timeout_ms is not None and timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        first = self.observe(request, status=status)
        if not first:
            return []
        if timeout_ms is None:
            refined = await refine(request)
            return first + self.revise_with(first[-1], request, refined)
        try:
            refined = await asyncio.wait_for(refine(request), timeout_ms / 1000.0)
        except asyncio.TimeoutError:
            self._stats.refine_timeouts += 1
            final = self.revise_with(first[-1], request, first, status="final")
            return first + final
        return first + self.revise_with(first[-1], request, refined)

    async def feed(
        self,
        events: AsyncIterable[DecisionRequest],
        *,
        coalesce_ms: int = 0,
    ) -> AsyncIterator[Decision]:
        """Observe an async event stream and yield its decisions.

        With ``coalesce_ms``, only the newest event is kept until the stream is
        quiet for that long; that is the debounce window for a busy source.
        """
        if coalesce_ms <= 0:
            async for event in events:
                for decision in self._admit(event, status="final", force=False, revision=0, supersedes=None):
                    yield decision
            return

        queue: asyncio.Queue[DecisionRequest | None] = asyncio.Queue()

        async def pump() -> None:
            try:
                async for event in events:
                    await queue.put(event)
            finally:
                await queue.put(None)

        task = asyncio.create_task(pump())
        pending: DecisionRequest | None = None
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=coalesce_ms / 1000.0)
                except asyncio.TimeoutError:
                    if pending is not None:
                        for decision in self._admit(
                            pending, status="final", force=False, revision=0, supersedes=None
                        ):
                            yield decision
                        pending = None
                    continue
                if event is None:
                    if pending is not None:
                        for decision in self._admit(
                            pending, status="final", force=False, revision=0, supersedes=None
                        ):
                            yield decision
                    break
                pending = event
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def feed_windows(
        self,
        events: AsyncIterable[DecisionRequest],
        *,
        window_ms: int,
        on_window: Callable[[WindowBatch], DecisionRequest | None],
        late: str = "drop",
    ) -> AsyncIterator[Decision]:
        """Aggregate events into tumbling windows, then decide each window."""
        window = TumblingWindow(window_ms, late=late)

        async def decide(batch: WindowBatch) -> AsyncIterator[Decision]:
            request = on_window(batch)
            if request is None:
                return
            for decision in self._admit(request, status="final", force=False, revision=0, supersedes=None):
                yield decision

        async for event in events:
            for batch in window.add(event):
                async for decision in decide(batch):
                    yield decision
        for batch in window.flush():
            async for decision in decide(batch):
                yield decision

    async def decisions(self) -> AsyncIterator[Decision]:
        """Yield buffered decisions in order until the session closes."""
        while True:
            if self._items:
                decision = self._items.popleft()
                self._space.set()
                yield decision
                continue
            if self._closed:
                return
            self._wake.clear()
            await self._wake.wait()

    async def observe_wait(
        self,
        request: DecisionRequest,
        *,
        status: str = "final",
        force: bool = False,
    ) -> list[Decision]:
        """Wait for buffer space, then observe; the async backpressure path."""
        while not self._closed and len(self._items) >= self._capacity:
            self._space.clear()
            await self._space.wait()
        return self.observe(request, status=status, force=force)


__all__ = ["FeedMixin", "Refiner"]
