"""Event-time windows: close a batch when the event clock leaves the window.

A window is a host-side aggregation helper.  LAIX still decides one task at a
time; the host turns a closed window into one ``DecisionRequest`` with
``on_window`` and feeds it to a stream session.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from ...core.domain.decisions import DecisionRequest
from ...core.support.time import parse_iso
from .window_batch import WindowBatch


class TumblingWindow:
    """Group events by event time into fixed, non-overlapping windows."""

    def __init__(self, window_ms: int, *, late: str = "drop") -> None:
        if window_ms <= 0:
            raise ValueError("window_ms must be positive")
        if late not in {"drop", "accept"}:
            raise ValueError(f"unknown late policy: {late!r}")
        self.window_ms = window_ms
        self.late = late
        self._start: datetime | None = None
        self._events: list[DecisionRequest] = []
        self._watermark: datetime | None = None

    def add(self, event: DecisionRequest) -> list[WindowBatch]:
        """Add one event and return any window it closes."""
        at = parse_iso(event.at)
        if at is None:
            raise ValueError(f"event has no valid at: {event.at!r}")

        if self._watermark is not None and at < self._watermark:
            if self.late == "drop":
                return []
        else:
            self._watermark = at

        start = self._window_start(at)
        batches: list[WindowBatch] = []
        if self._start is None:
            self._start = start
        elif start > self._start:
            batches.append(self._close())
            self._start = start
        elif start < self._start and self.late == "drop":
            return []

        self._events.append(event)
        return batches

    def flush(self) -> list[WindowBatch]:
        """Close the current window, if it has events."""
        if not self._events:
            return []
        return [self._close()]

    @property
    def pending(self) -> int:
        return len(self._events)

    def _close(self) -> WindowBatch:
        assert self._start is not None
        batch = WindowBatch(
            start=self._start,
            end=self._start + timedelta(milliseconds=self.window_ms),
            events=tuple(self._events),
        )
        self._events = []
        return batch

    def _window_start(self, at: datetime) -> datetime:
        seconds = self.window_ms / 1000.0
        epoch = at.timestamp()
        start = math.floor(epoch / seconds) * seconds
        return datetime.fromtimestamp(start, tz=timezone.utc)


__all__ = ["TumblingWindow", "WindowBatch"]
