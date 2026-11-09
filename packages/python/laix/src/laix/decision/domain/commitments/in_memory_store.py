"""A process-local commitment store, useful in tests."""

from __future__ import annotations

import json

from .ledger import CommitmentLedger


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


__all__ = ["InMemoryCommitmentStore"]
