"""Storage-free state store contracts.

The app owns the database. LAIX defines the save, load and delete interface so
an experience snapshot can outlive one request without LAIX becoming a memory
product.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .state import ExperienceState


@runtime_checkable
class StateStore(Protocol):
    def save(self, key: str, state: ExperienceState) -> None:
        ...

    def load(self, key: str) -> ExperienceState | None:
        ...

    def delete(self, key: str) -> None:
        ...


class InMemoryStateStore:
    """A small store for tests and local runs."""

    def __init__(self) -> None:
        self._items: dict[str, ExperienceState] = {}

    def save(self, key: str, state: ExperienceState) -> None:
        self._items[key] = state

    def load(self, key: str) -> ExperienceState | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)


__all__ = ["InMemoryStateStore", "StateStore"]
