"""Durable checkpoints for a stream session, without a database dependency."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StreamCheckpointStore(Protocol):
    """Save, load and delete one stream snapshot."""

    def save(self, key: str, snapshot: dict[str, Any]) -> None:
        ...

    def load(self, key: str) -> dict[str, Any] | None:
        ...

    def delete(self, key: str) -> None:
        ...


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


class FileStreamCheckpointStore:
    """One JSON file per stream, under a host-owned directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "".join(
            "_" if character in '/\\:*?"<>|' else character
            for character in key
        )
        return self.directory / f"{safe}.json"

    def save(self, key: str, snapshot: dict[str, Any]) -> None:
        path = self._path(key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        temporary.replace(path)

    def load(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


__all__ = [
    "FileStreamCheckpointStore",
    "InMemoryStreamCheckpointStore",
    "StreamCheckpointStore",
]
