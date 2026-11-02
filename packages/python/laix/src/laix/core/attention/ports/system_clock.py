"""A clock backed by the host process clock."""

from __future__ import annotations

from datetime import datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()


__all__ = ["SystemClock"]
