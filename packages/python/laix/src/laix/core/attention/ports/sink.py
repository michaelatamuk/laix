"""The sink port: deliver one accepted notification."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Sink(Protocol):
    """Deliver one accepted notification. Returns one record per channel."""

    def emit(self, notification: Mapping[str, Any]) -> list[Mapping[str, Any]]: ...


__all__ = ["Sink"]
