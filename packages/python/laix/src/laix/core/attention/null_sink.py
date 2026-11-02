"""A sink that records the decision and delivers nothing."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class NullSink:
    """A sink that records the decision and delivers nothing. Useful in tests."""

    def __init__(self) -> None:
        self.seen: list[Mapping[str, Any]] = []

    def emit(self, notification: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        self.seen.append(notification)
        return [{"channel": "none", "status": "dropped"}]


__all__ = ["NullSink"]
