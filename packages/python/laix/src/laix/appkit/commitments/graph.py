"""Build a commitment graph from a local ledger and a resolver."""

from __future__ import annotations

from ...decision.domain.commitments import (
    CommitmentGraph,
    CommitmentLedger,
    CommitmentRef,
)
from .port import AsyncCommitmentResolver, CommitmentResolver


def _external_refs(local: CommitmentLedger) -> tuple[CommitmentRef, ...]:
    return tuple(
        dict.fromkeys(
            ref for item in local.all() for ref in item.external_depends_on
        )
    )


def resolve_commitment_graph(
    local: CommitmentLedger,
    resolver: CommitmentResolver,
) -> CommitmentGraph:
    """Resolve every external reference in ``local`` and return its graph.

    The resolver may return fewer commitments than requested. The graph then
    reports the unresolved references through ``missing_refs``.
    """
    return CommitmentGraph(local, resolver.resolve(_external_refs(local)))


async def resolve_commitment_graph_async(
    local: CommitmentLedger,
    resolver: AsyncCommitmentResolver,
) -> CommitmentGraph:
    """Async variant of :func:`resolve_commitment_graph`."""
    return CommitmentGraph(local, await resolver.resolve(_external_refs(local)))


__all__ = ["resolve_commitment_graph", "resolve_commitment_graph_async"]
