"""The recorder port: persist one labelled outcome."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Recorder(Protocol):
    """Persist one labelled outcome."""

    def record(self, outcome: Mapping[str, Any]) -> None: ...


__all__ = ["Recorder"]
