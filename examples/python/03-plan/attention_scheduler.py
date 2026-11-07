"""AADS: rank pending decisions for scarce human attention."""

from __future__ import annotations

from laix import AttentionCandidate, AttentionScheduler

schedule = AttentionScheduler().schedule(
    (
        AttentionCandidate(
            id="refund-approval",
            risk=0.9,
            commitment=True,
            information_value=0.4,
            review_cost=1.0,
            deadline="2026-11-01T10:05:00+00:00",
        ),
        AttentionCandidate(
            id="routine-review",
            risk=0.2,
            review_cost=1.0,
            deadline="2026-11-01T12:00:00+00:00",
        ),
        AttentionCandidate(
            id="check-evidence",
            risk=0.4,
            information_value=0.6,
            review_cost=0.5,
        ),
    ),
    now="2026-11-01T10:00:00+00:00",
    budget=1.5,
)

print(",".join(row.candidate_id for row in schedule.selected))
print(",".join(row.candidate_id for row in schedule.deferred))
print(schedule.spent, schedule.budget)
