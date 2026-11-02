"""The clock port: the module never reads the environment itself."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


__all__ = ["Clock"]
