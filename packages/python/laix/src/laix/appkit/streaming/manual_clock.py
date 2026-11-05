"""A clock the caller moves."""

from __future__ import annotations

from datetime import datetime

from ...core.support.time import utcnow


class ManualClock:
    """A clock the caller moves.  Used by replay and deterministic tests."""

    def __init__(self, now: datetime | None = None) -> None:
        self.now = now or utcnow()

    def __call__(self) -> datetime:
        return self.now

    def set(self, value: datetime) -> None:
        self.now = value


__all__ = ["ManualClock"]
