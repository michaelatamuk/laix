"""Commitments and the planning policy."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import (
    Commitment,
    CommitmentLedger,
    DecisionRequest,
    FileCommitmentStore,
    InMemoryCommitmentStore,
    PlanningPolicy,
)

NOW = datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc)


def _request(at: str = "2026-11-01T10:00:00+00:00") -> DecisionRequest:
    return DecisionRequest(subject="a task", at=at)


def test_next_commitment_and_blocking() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="first", due="2026-11-01T09:00:00+00:00"),
            Commitment(id="b", subject="second", due="2026-11-01T11:00:00+00:00", depends_on=("a",)),
        )
    )

    assert ledger.next(NOW).id == "a"
    assert ledger.blocked(ledger.get("b")) is True
    ledger.complete("a")
    assert ledger.blocked(ledger.get("b")) is False


def test_planning_policy_acts_on_a_due_commitment() -> None:
    ledger = CommitmentLedger(
        (Commitment(id="a", subject="first", due="2026-11-01T09:00:00+00:00"),)
    )
    decision = PlanningPolicy(ledger).decide(_request())[0]

    assert decision.verb == "act"
    assert decision.reason_code == "due_commitment"
    assert decision.action_id == "a"


def test_planning_policy_asks_when_blocked() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(id="a", subject="first", due="2026-11-01T09:00:00+00:00"),
            Commitment(id="b", subject="second", due="2026-11-01T09:00:00+00:00", depends_on=("a",)),
        )
    )
    first = PlanningPolicy(ledger).decide(_request())[0]
    assert first.verb == "act"

    # The first is chosen; make it blocked to test the ask path.
    ledger.add(Commitment(id="a", subject="first", due="2026-11-01T09:00:00+00:00", depends_on=("missing",)))
    decision = PlanningPolicy(ledger).decide(_request())[0]
    assert decision.verb == "ask"
    assert decision.reason_code == "blocked_commitment"


def test_planning_policy_skips_a_blocked_commitment() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(
                id="a",
                subject="blocked first",
                due="2026-11-01T09:00:00+00:00",
                depends_on=("missing",),
            ),
            Commitment(id="b", subject="ready second", due="2026-11-01T09:30:00+00:00"),
        )
    )

    assert ledger.blocked_open() == (ledger.get("a"),)
    assert ledger.next_actionable(NOW).id == "b"
    decision = PlanningPolicy(ledger).decide(_request())[0]
    assert decision.verb == "act"
    assert decision.action_id == "b"


def test_commitment_ledger_round_trips_through_a_store() -> None:
    ledger = CommitmentLedger(
        (
            Commitment(
                id="a",
                subject="first",
                due="2026-11-01T09:00:00+00:00",
                priority=0.8,
                payload={"owner": "alice"},
            ),
        )
    )
    store = InMemoryCommitmentStore()
    store.save("task-1", ledger)

    restored = store.load("task-1")
    assert restored is not None
    assert restored.get("a").payload == {"owner": "alice"}
    assert restored.get("a").priority == 0.8

    store.delete("task-1")
    assert store.load("task-1") is None


def test_file_commitment_store_round_trips(tmp_path) -> None:
    ledger = CommitmentLedger((Commitment(id="a", subject="first"),))
    store = FileCommitmentStore(tmp_path)
    store.save("task-1", ledger)

    restored = store.load("task-1")
    assert restored is not None
    assert restored.get("a").subject == "first"

    store.delete("task-1")
    assert store.load("task-1") is None
