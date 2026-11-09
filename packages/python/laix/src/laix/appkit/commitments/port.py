"""The port a host implements to supply another owner's commitments."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable

from ...decision.domain.commitments import Commitment, CommitmentRef


@runtime_checkable
class CommitmentResolver(Protocol):
    """Resolve owner-qualified references from host-managed state.

    The port is synchronous on purpose: LAIX never performs network I/O while
    planning. A host with a remote source resolves into a local cache first and
    serves this call from there.
    """

    def resolve(self, refs: Iterable[CommitmentRef]) -> tuple[Commitment, ...]:
        ...


@runtime_checkable
class AsyncCommitmentResolver(Protocol):
    """An async variant for hosts that fetch before planning."""

    async def resolve(self, refs: Iterable[CommitmentRef]) -> tuple[Commitment, ...]:
        ...


__all__ = ["AsyncCommitmentResolver", "CommitmentResolver"]
