"""What an app supplies when outcomes outlive one request."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .record import Outcome


@runtime_checkable
class OutcomeStore(Protocol):
    """What an app supplies when outcomes outlive one request."""

    def add(self, outcome: Outcome) -> Outcome:
        ...

    def for_decision(self, decision_id: str) -> list[Outcome]:
        ...

    def all(self) -> list[Outcome]:
        ...

    def summary(self) -> dict[str, Any]:
        ...


__all__ = ["OutcomeStore"]
