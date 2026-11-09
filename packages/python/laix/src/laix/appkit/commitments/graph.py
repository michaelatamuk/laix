"""Build a commitment graph from a local ledger and a resolver."""

from __future__ import annotations

from ...decision.domain.commitments import (
    CommitmentGraph,
    CommitmentLedger,
    CommitmentRef,
)
from .port import CommitmentResolver


def resolve_commitment_graph(
    local: CommitmentLedger,
    resolver: CommitmentResolver,
) -> CommitmentGraph:
    """Resolve every external reference in ``local`` and return its graph.

    The resolver may return fewer commitments than requested. The graph then
    reports the unresolved references through ``missing_refs``.
    """
    refs: tuple[CommitmentRef, ...] = tuple(
        dict.fromkeys(
            ref for item in local.all() for ref in item.external_depends_on
        )
    )
    return CommitmentGraph(local, resolver.resolve(refs))


__all__ = ["resolve_commitment_graph"]
