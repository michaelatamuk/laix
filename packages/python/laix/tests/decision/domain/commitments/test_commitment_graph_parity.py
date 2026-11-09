"""Shared commitment-graph cases, consumed by Python and TypeScript."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from laix import Commitment, CommitmentGraph, CommitmentLedger, CommitmentRef

ROOT = Path(__file__).resolve().parents[7]
FIXTURE = ROOT / "packages" / "contracts" / "commitment-graph.v1.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_commitment_graph_fixture(case: dict[str, object]) -> None:
    expected = case["expected"]
    assert isinstance(expected, dict)
    local = CommitmentLedger(
        tuple(Commitment.from_dict(item) for item in case["local"])  # type: ignore[arg-type]
    )
    external = tuple(
        Commitment.from_dict(item) for item in case["external"]  # type: ignore[union-attr]
    )
    graph = CommitmentGraph(local, external)
    target = local.get(str(case["target"]))

    assert graph.blocked(target) is expected["blocked"]
    assert graph.blocked(target, require_verified=True) is expected["blocked_verified"]
    assert [
        {
            "owner": blocker.ref.owner,
            "ledger": blocker.ref.ledger,
            "id": blocker.ref.id,
            "reason": blocker.reason,
        }
        for blocker in graph.blockers(target, require_verified=True)
    ] == expected["blockers"]
    assert [ref.to_dict() for ref in graph.missing_refs()] == expected["missing_refs"]
    assert [ref.to_dict() for ref in graph.unverified_refs()] == expected["unverified_refs"]

    if "chain" in expected:
        chain_ref = CommitmentRef(owner="local", ledger=None, id=str(case["chain_from"]))
        assert [item.id for item in graph.chain(chain_ref)] == expected["chain"]
    if "impact" in expected:
        impact_ref = CommitmentRef(owner="local", ledger=None, id=str(case["impact_from"]))
        assert [item.id for item in graph.impact(impact_ref)] == expected["impact"]
    if "critical_path" in expected:
        assert [item.id for item in graph.critical_path()] == expected["critical_path"]
    if "cycles" in expected:
        actual = {frozenset(ref.id for ref in cycle) for cycle in graph.cycles()}
        wanted = {frozenset(cycle) for cycle in expected["cycles"]}
        assert actual == wanted
