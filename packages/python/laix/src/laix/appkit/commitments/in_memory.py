"""An in-memory resolver for tests and short-lived tasks."""

from __future__ import annotations

from collections.abc import Iterable

from ...decision.domain.commitments import Commitment, CommitmentRef


class InMemoryCommitmentResolver:
    """Resolve from commitments already held by the host."""

    def __init__(self, commitments: Iterable[Commitment] = ()) -> None:
        self._items: dict[tuple[str, str, str], Commitment] = {}
        for item in commitments:
            self._items[item.key] = item

    def add(self, commitment: Commitment) -> Commitment:
        self._items[commitment.key] = commitment
        return commitment

    def resolve(self, refs: Iterable[CommitmentRef]) -> tuple[Commitment, ...]:
        found: list[Commitment] = []
        for ref in refs:
            item = self._items.get(ref.key)
            if item is not None:
                found.append(item)
        return tuple(found)


__all__ = ["InMemoryCommitmentResolver"]
