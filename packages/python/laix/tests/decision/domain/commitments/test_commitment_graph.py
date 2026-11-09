"""Commitment graphs across owners and the planner's trust boundary."""

from __future__ import annotations

from laix import (
    ActionOption,
    Commitment,
    CommitmentGraph,
    CommitmentLedger,
    CommitmentPlanner,
    CommitmentRef,
    PlannerInput,
)


def _supplier_ref() -> CommitmentRef:
    return CommitmentRef(owner="supplier", ledger="supplier", id="c2")


def test_external_dependency_and_verification() -> None:
    local = CommitmentLedger(
        (
            Commitment(
                id="c1",
                subject="deliver to the customer",
                external_depends_on=(_supplier_ref(),),
            ),
        )
    )
    reported = Commitment(
        id="c2",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source="reported",
    )
    graph = CommitmentGraph(local, (reported,))

    assert graph.blocked(local.get("c1")) is False
    assert graph.blocked(local.get("c1"), require_verified=True) is True
    assert [(item.ref.id, item.reason) for item in graph.blockers(
        local.get("c1"), require_verified=True
    )] == [("c2", "unverified")]
    assert [item.id for item in graph.unverified_refs()] == ["c2"]

    verified = Commitment(
        id="c2",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source="verified",
        verified_at="2026-11-01T09:00:00+00:00",
    )
    graph = CommitmentGraph(local, (verified,))
    assert graph.blocked(local.get("c1"), require_verified=True) is False


def test_missing_refs_and_cycles() -> None:
    missing = CommitmentRef(owner="other", ledger="other", id="x")
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="a", external_depends_on=(missing,)),
            Commitment(id="b", subject="b", depends_on=("c",)),
            Commitment(id="c", subject="c", depends_on=("b",)),
        )
    )
    graph = CommitmentGraph(ledger)

    assert graph.missing_refs() == (missing,)
    assert graph.cycles()
    assert {item.id for item in graph.cycles()[0]} == {"b", "c"}


def test_impact_and_chain() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="a"),
            Commitment(id="b", subject="b", depends_on=("a",)),
            Commitment(id="c", subject="c", depends_on=("b",)),
        )
    )
    graph = CommitmentGraph(ledger)

    assert [item.id for item in graph.impact(CommitmentRef("local", "a"))] == ["b", "c"]
    assert [item.id for item in graph.chain(CommitmentRef("local", "c"))] == ["c", "b", "a"]
    assert [item.id for item in graph.critical_path()] == ["c", "b", "a"]


def test_planner_blocks_a_hard_commitment_on_an_unverified_dependency() -> None:
    local = CommitmentLedger(
        (
            Commitment(
                id="c1",
                subject="deliver to the customer",
                external_depends_on=(_supplier_ref(),),
            ),
        )
    )
    reported = Commitment(
        id="c2",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source="reported",
    )
    graph = CommitmentGraph(local, (reported,))
    problem = PlannerInput(
        subject="deliver",
        at="2026-11-01T10:00:00+00:00",
        options=(
            ActionOption(
                id="finish",
                verb="act",
                name="finish the delivery",
                expected_benefit=1.0,
                params={"commitments": {"fulfills": ["c1"], "hard": True}},
            ),
            ActionOption(
                id="wait",
                verb="wait",
                name="wait for verification",
                expected_benefit=0.1,
            ),
        ),
        attributes={"commitment_graph": graph},
    )

    result = CommitmentPlanner().solve(problem)

    assert result.action_id == "wait"
    assert "blocked hard commitment" in result.alternatives[0]["rejected_because"]


def test_commitment_round_trips_owner_and_external_refs() -> None:
    commitment = Commitment(
        id="c1",
        subject="deliver",
        owner="supplier",
        ledger="supplier",
        source="reported",
        verified_at="2026-11-01T09:00:00+00:00",
        external_depends_on=(CommitmentRef("other", "x", "other"),),
    )

    assert Commitment.from_dict(commitment.to_dict()) == commitment
