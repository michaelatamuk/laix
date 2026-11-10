# CDR: continuity decision repair

`repair_continuity` finds explicit conflicts and rule-derived conflicts in a decision history. It
supersedes the cheaper side of each conflict.

```python
from laix import ContinuityRecord, repair_continuity

plan = repair_continuity(
    (
        ContinuityRecord(id="approval-1", kind="approval", status="rejected", refs=("order-1",), cost=1.0),
        ContinuityRecord(id="receipt-1", kind="receipt", status="executed", refs=("order-1",), cost=3.0),
    )
)
print(plan.actions)
```

`consistent` reports whether the input history was already consistent; a plan with conflicts still
contains the actions that repair them.

The default repair is greedy. Pass `exact=True` to solve the minimum-weight vertex cover over the
conflict graph by branch and bound:

```python
from laix import repair_continuity

plan = repair_continuity(records, exact=True)
print(plan.total_cost, [action.record_id for action in plan.actions])
```

The exact path is exponential in the worst case but fast on small decision histories. The full
method remains incremental truth maintenance with a weighted MaxSAT repair.

## Related

- [History overview](README.md)
- [Continuity](01-continuity.md)
- [Revalidation](03-revalidation.md)
