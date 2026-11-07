"""CDR: repair an inconsistent decision history at minimum cost."""

from __future__ import annotations

from laix import ContinuityRecord, repair_continuity

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

print(plan.conflicts)
print([(action.record_id, action.action, action.to_status) for action in plan.actions])
print(plan.total_cost)
