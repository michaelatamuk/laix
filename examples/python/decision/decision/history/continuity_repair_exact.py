"""CDR exact repair: minimum-weight vertex cover beats the greedy choice."""

from __future__ import annotations

from laix import ContinuityRecord, repair_continuity

records = (
    ContinuityRecord(id="a", kind="decision", status="final", conflicts=("b",), cost=1.0),
    ContinuityRecord(id="b", kind="decision", status="final", conflicts=("c", "d"), cost=2.0),
    ContinuityRecord(id="c", kind="decision", status="final", cost=1.0),
    ContinuityRecord(id="d", kind="decision", status="final", cost=1.0),
)

greedy = repair_continuity(records)
exact = repair_continuity(records, exact=True)

print(greedy.total_cost, exact.total_cost, [action.record_id for action in exact.actions])
