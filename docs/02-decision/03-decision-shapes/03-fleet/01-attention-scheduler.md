# Attention scheduler

`AttentionScheduler` ranks pending decisions with a Whittle-style index:

```text
index = (expected_gain * urgency - waiting_cost) / review_cost
```

The caller supplies risk, deadline, commitment flag, information value, waiting cost and review cost.
The scheduler allocates the attention budget in index order.

```python
from laix import AttentionCandidate, AttentionScheduler

schedule = AttentionScheduler().schedule(
    (
        AttentionCandidate(id="refund", risk=0.9, commitment=True, deadline="2026-11-01T10:05:00+00:00"),
        AttentionCandidate(id="routine", risk=0.2),
    ),
    now="2026-11-01T10:00:00+00:00",
    budget=1.0,
)
print([row.candidate_id for row in schedule.selected])
```

## Related

- [Fleet overview](README.md)
- [Whittle scheduler](02-whittle.md)
