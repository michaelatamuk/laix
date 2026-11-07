from __future__ import annotations

from laix import ContinuityRecord, repair_continuity


def test_repair_supersedes_the_cheaper_conflicting_record() -> None:
    plan = repair_continuity(
        (
            ContinuityRecord(
                id="approval-1",
                kind="approval",
                status="rejected",
                refs=("order-1",),
                cost=1.0,
            ),
            ContinuityRecord(
                id="receipt-1",
                kind="receipt",
                status="executed",
                refs=("order-1",),
                cost=3.0,
            ),
        )
    )

    assert plan.conflicts == (("approval-1", "receipt-1"),)
    assert plan.actions[0].record_id == "approval-1"
    assert plan.actions[0].to_status == "superseded"
    assert plan.total_cost == 1.0
    assert plan.consistent is False


def test_repair_is_empty_for_a_consistent_history() -> None:
    plan = repair_continuity(
        (
            ContinuityRecord(id="decision-1", kind="decision", status="final"),
        )
    )

    assert plan.conflicts == ()
    assert plan.actions == ()
    assert plan.total_cost == 0.0
    assert plan.consistent is True


def test_explicit_conflicts_are_honoured() -> None:
    plan = repair_continuity(
        (
            ContinuityRecord(
                id="a",
                kind="decision",
                status="final",
                conflicts=("b",),
                cost=0.1,
            ),
            ContinuityRecord(
                id="b",
                kind="decision",
                status="final",
                cost=0.2,
            ),
        )
    )

    assert plan.actions[0].record_id == "a"
