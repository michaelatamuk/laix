"""The app-kit resolver port feeds a commitment graph."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from laix import (
    AsyncCommitmentResolver,
    Commitment,
    CommitmentLedger,
    CommitmentRef,
    CommitmentResolver,
    InMemoryCommitmentResolver,
    resolve_commitment_graph,
    resolve_commitment_graph_async,
)


def _ship(*, source: str = "verified") -> Commitment:
    return Commitment(
        id="ship",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source=source,
        verified_at=(
            "2026-11-01T09:30:00+00:00" if source == "verified" else None
        ),
    )


def _local() -> CommitmentLedger:
    return CommitmentLedger(
        (
            Commitment(
                id="deliver",
                subject="deliver to the customer",
                external_depends_on=(
                    CommitmentRef(owner="supplier", ledger="supplier", id="ship"),
                ),
            ),
        )
    )


def test_resolver_builds_a_verified_graph() -> None:
    resolver = InMemoryCommitmentResolver((_ship(),))
    local = _local()
    graph = resolve_commitment_graph(local, resolver)

    assert isinstance(resolver, CommitmentResolver)
    assert graph.get(
        CommitmentRef(owner="supplier", ledger="supplier", id="ship")
    ) is not None
    assert graph.blocked(local.get("deliver"), require_verified=True) is False
    assert graph.missing_refs() == ()


def test_resolver_reports_a_missing_commitment() -> None:
    local = _local()
    graph = resolve_commitment_graph(local, InMemoryCommitmentResolver())

    assert graph.blocked(local.get("deliver"), require_verified=True) is True
    assert graph.missing_refs() == (
        CommitmentRef(owner="supplier", ledger="supplier", id="ship"),
    )


def test_resolver_keeps_a_reported_commitment_unverified() -> None:
    local = _local()
    graph = resolve_commitment_graph(
        local, InMemoryCommitmentResolver((_ship(source="reported"),))
    )

    assert graph.blocked(local.get("deliver"), require_verified=True) is True
    assert [ref.id for ref in graph.unverified_refs()] == ["ship"]


class _AsyncResolver:
    async def resolve(self, _refs: Iterable[CommitmentRef]) -> tuple[Commitment, ...]:
        return (_ship(),)


def test_async_resolver_builds_a_graph() -> None:
    local = _local()
    resolver = _AsyncResolver()

    assert isinstance(resolver, AsyncCommitmentResolver)
    graph = asyncio.run(resolve_commitment_graph_async(local, resolver))
    assert graph.blocked(local.get("deliver"), require_verified=True) is False
