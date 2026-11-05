"""Commitments and the planning policy."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import (
    Commitment,
    CommitmentLedger,
    DecisionRequest,
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
