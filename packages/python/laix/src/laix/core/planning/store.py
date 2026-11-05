"""Commitment stores: keep a task's plan without owning the app database."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from .commitment import CommitmentLedger


@runtime_checkable
class CommitmentStore(Protocol):
    """Save, load and delete one commitment ledger."""

    def save(self, key: str, ledger: CommitmentLedger) -> None:
        ...

    def load(self, key: str) -> CommitmentLedger | None:
        ...

    def delete(self, key: str) -> None:
        ...


class InMemoryCommitmentStore:
    """A process-local store, useful in tests."""

    def __init__(self) -> None:
        self._items: dict[str, dict] = {}

    def save(self, key: str, ledger: CommitmentLedger) -> None:
        self._items[key] = json.loads(json.dumps(ledger.to_dict()))

    def load(self, key: str) -> CommitmentLedger | None:
        payload = self._items.get(key)
        return None if payload is None else CommitmentLedger.from_dict(payload)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)


class FileCommitmentStore:
    """One JSON file per ledger, under a host-owned directory."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "".join(
            "_" if character in '/\\:*?"<>|' else character
            for character in key
        )
        return self.directory / f"{safe}.json"

    def save(self, key: str, ledger: CommitmentLedger) -> None:
        path = self._path(key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(ledger.to_dict(), indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def load(self, key: str) -> CommitmentLedger | None:
        path = self._path(key)
        if not path.exists():
            return None
        return CommitmentLedger.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)


__all__ = [
    "CommitmentStore",
    "FileCommitmentStore",
    "InMemoryCommitmentStore",
]
