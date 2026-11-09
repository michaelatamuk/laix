"""Commitment graphs across owners and the planner's trust boundary."""

from __future__ import annotations

from datetime import datetime, timedelta

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


def _verified_shipment(verified_at: str) -> Commitment:
    return Commitment(
        id="c2",
        subject="ship the part",
        owner="supplier",
        ledger="supplier",
        status="done",
        source="verified",
        verified_at=verified_at,
    )


def test_stale_verification_blocks_with_max_age() -> None:
    now = datetime.fromisoformat("2026-11-01T10:00:00+00:00")
    local = CommitmentLedger(
        (
            Commitment(
                id="c1",
                subject="deliver",
                external_depends_on=(_supplier_ref(),),
            ),
        )
    )
    graph = CommitmentGraph(local, (_verified_shipment("2026-10-31T09:00:00+00:00"),))

    assert graph.blocked(local.get("c1"), require_verified=True) is False
    assert (
        graph.blocked(
            local.get("c1"),
            require_verified=True,
            now=now,
            max_verification_age=timedelta(hours=24),
        )
        is True
    )
    assert [
        blocker.reason
        for blocker in graph.blockers(
            local.get("c1"),
            require_verified=True,
            now=now,
            max_verification_age=timedelta(hours=24),
        )
    ] == ["stale"]
    assert graph.stale_refs(now, timedelta(hours=24)) == (_supplier_ref(),)


def test_fresh_verification_passes_with_max_age() -> None:
    now = datetime.fromisoformat("2026-11-01T10:00:00+00:00")
    local = CommitmentLedger(
        (
            Commitment(
                id="c1",
                subject="deliver",
                external_depends_on=(_supplier_ref(),),
            ),
        )
    )
    graph = CommitmentGraph(local, (_verified_shipment("2026-11-01T09:30:00+00:00"),))

    assert (
        graph.blocked(
            local.get("c1"),
            require_verified=True,
            now=now,
            max_verification_age=timedelta(hours=24),
        )
        is False
    )
    assert graph.stale_refs(now, timedelta(hours=24)) == ()


def test_planner_rejects_a_stale_verification() -> None:
    now = "2026-11-01T10:00:00+00:00"
    local = CommitmentLedger(
        (
            Commitment(
                id="c1",
                subject="deliver",
                external_depends_on=(_supplier_ref(),),
            ),
        )
    )
    graph = CommitmentGraph(local, (_verified_shipment("2026-10-30T09:00:00+00:00"),))
    problem = PlannerInput(
        subject="deliver",
        at=now,
        options=(
            ActionOption(
                id="finish",
                verb="act",
                name="finish",
                expected_benefit=1.0,
                params={"commitments": {"fulfills": ["c1"], "hard": True}},
            ),
            ActionOption(
                id="wait",
                verb="wait",
                name="wait",
                expected_benefit=0.1,
            ),
        ),
        attributes={"commitment_graph": graph},
    )

    result = CommitmentPlanner(
        max_verification_age=timedelta(hours=24)
    ).solve(problem)

    assert result.action_id == "wait"
    assert result.alternatives[0]["blocked_by"] == [
        {
            "owner": "supplier",
            "ledger": "supplier",
            "id": "c2",
            "reason": "stale",
        }
    ]


def test_subgraph_neighborhood_and_redaction() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="a", payload={"secret": 1}),
            Commitment(id="b", subject="b", depends_on=("a",)),
            Commitment(id="c", subject="c", depends_on=("b",)),
        )
    )
    graph = CommitmentGraph(ledger)

    assert [item.id for item in graph.subgraph([CommitmentRef("local", "a")]).commitments] == ["a"]
    assert [
        item.id for item in graph.neighborhood(CommitmentRef("local", "b")).commitments
    ] == ["a", "b", "c"]

    redacted = graph.redacted()
    assert {item.subject for item in redacted.commitments} == {""}
    assert {tuple(item.payload) for item in redacted.commitments} == {()}

    kept = graph.redacted(keep_subject=True)
    assert {item.subject for item in kept.commitments} == {"a", "b", "c"}


def test_validate_reports_missing_cycles_and_stale_refs() -> None:
    now = datetime.fromisoformat("2026-11-01T10:00:00+00:00")
    missing = CommitmentRef(owner="other", ledger="other", id="x")
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="a", external_depends_on=(missing,)),
            Commitment(id="b", subject="b", depends_on=("c",)),
            Commitment(id="c", subject="c", depends_on=("b",)),
        )
    )
    graph = CommitmentGraph(ledger, (_verified_shipment("2026-10-01T09:00:00+00:00"),))

    report = graph.validate(now=now, max_verification_age=timedelta(days=1))

    assert report.missing_refs == (missing,)
    assert report.cycles
    assert [ref.id for ref in report.stale_refs] == ["c2"]


def test_graph_exports_mermaid_and_dot() -> None:
    graph = CommitmentGraph(
        CommitmentLedger(
            (
                Commitment(id="a", subject="a"),
                Commitment(id="b", subject="b", depends_on=("a",)),
            )
        ),
        (_verified_shipment("2026-11-01T09:30:00+00:00"),),
    )

    mermaid = graph.to_mermaid()
    assert mermaid.startswith("flowchart LR")
    assert "depends_on" in mermaid
    assert 'n0["local · a · a · open"]' in mermaid

    dot = graph.to_dot()
    assert dot.startswith("digraph commitments {")
    assert 'label="depends_on"' in dot
