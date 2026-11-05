"""Plan the next move from a commitment ledger."""

from __future__ import annotations

from laix import Commitment, CommitmentLedger, DecisionRequest, PlanningPolicy

ledger = CommitmentLedger(
    (Commitment(id="a", subject="send the draft", due="2026-11-01T09:00:00+00:00"),)
)
decision = PlanningPolicy(ledger).decide(
    DecisionRequest(subject="the task", at="2026-11-01T10:00:00+00:00")
)[0]
print(decision.verb, decision.reason_code, decision.action_id)
