"""Commitment stores: keep a task's plan without owning the app database."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .commitment import CommitmentLedger
from .file_commitment_store import FileCommitmentStore
from .in_memory_commitment_store import InMemoryCommitmentStore


@runtime_checkable
class CommitmentStore(Protocol):
    """Save, load and delete one commitment ledger."""

    def save(self, key: str, ledger: CommitmentLedger) -> None:
        ...

    def load(self, key: str) -> CommitmentLedger | None:
        ...

    def delete(self, key: str) -> None:
        ...


__all__ = [
    "CommitmentStore",
    "FileCommitmentStore",
    "InMemoryCommitmentStore",
]
