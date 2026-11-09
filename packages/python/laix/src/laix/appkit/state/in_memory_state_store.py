"""A small in-memory store for tests and local runs."""

from __future__ import annotations

from .state import ExperienceState


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


__all__ = ["InMemoryStateStore"]
