"""Shared commitment-graph cases, consumed by Python and TypeScript."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from laix import (
    ActionOption,
    Commitment,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    PlannerInput,
)

ROOT = Path(__file__).resolve().parents[7]
FIXTURE = ROOT / "packages" / "contracts" / "commitment-graph.v1.json"
PAYLOAD = json.loads(FIXTURE.read_text(encoding="utf-8"))
CASES = PAYLOAD["cases"]
PLANNER_CASES = PAYLOAD["planner_cases"]


def _ledger(items: object) -> CommitmentLedger:
    return CommitmentLedger(
        tuple(
            Commitment.from_dict(item)
            for item in items  # type: ignore[union-attr]
        )
    )


def _option(raw: dict[str, object]) -> ActionOption:
    return ActionOption(
        id=str(raw["id"]),
        verb=str(raw["verb"]),
        name=str(raw["name"]),
        expected_benefit=float(raw.get("expected_benefit", 0.5)),
        params=dict(raw.get("params", {})),  # type: ignore[arg-type]
    )


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


@pytest.mark.parametrize("case", PLANNER_CASES, ids=lambda case: case["id"])
def test_commitment_planner_fixture(case: dict[str, object]) -> None:
    graph = CommitmentGraph(
        _ledger(case["local"]),
        tuple(
            Commitment.from_dict(item)
            for item in case["external"]  # type: ignore[union-attr]
        ),
    )
    problem = PlannerInput(
        subject="deliver",
        at="2026-11-01T10:00:00+00:00",
        options=tuple(
            _option(item)
            for item in case["options"]  # type: ignore[union-attr]
        ),
        attributes={"commitment_graph": graph},
    )
    result = CommitmentPlanner(
        require_verified=bool(case["require_verified"])
    ).solve(problem)

    assert result.action_id == case["expected_action_id"]
    if result.action_id == "finish":
        assert (
            result.attributes["commitments_blocked_by"]
            == case["expected_blocked_by"]
        )
    else:
        finish = next(
            row for row in result.alternatives if row["action_id"] == "finish"
        )
        assert finish["blocked_by"] == case["expected_blocked_by"]


def test_graph_round_trips_through_dict() -> None:
    graph = CommitmentGraph(
        CommitmentLedger((Commitment(id="a", subject="a"),)),
        (
            Commitment(
                id="b",
                subject="b",
                owner="other",
                ledger="other",
                source="reported",
            ),
        ),
    )
    restored = CommitmentGraph.from_dict(graph.to_dict())

    assert restored.to_dict() == graph.to_dict()
    assert [item.id for item in restored.commitments] == ["a", "b"]
