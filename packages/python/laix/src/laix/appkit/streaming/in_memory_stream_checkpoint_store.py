"""A process-local checkpoint store, useful in tests."""

from __future__ import annotations

import json
from typing import Any


class InMemoryStreamCheckpointStore:
    """A process-local checkpoint store, useful in tests."""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def save(self, key: str, snapshot: dict[str, Any]) -> None:
        self._items[key] = json.loads(json.dumps(snapshot))

    def load(self, key: str) -> dict[str, Any] | None:
        item = self._items.get(key)
        return json.loads(json.dumps(item)) if item is not None else None

    def delete(self, key: str) -> None:
        self._items.pop(key, None)


__all__ = ["InMemoryStreamCheckpointStore"]
