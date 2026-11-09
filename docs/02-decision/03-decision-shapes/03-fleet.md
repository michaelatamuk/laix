# Fleet attention

Fleet attention answers a different question from a single planner: many pending decisions compete for
the same humans. Which decision should receive attention now, and which should wait?

## AADS: attention-aware decision scheduling

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

## Exact Whittle index

`WhittleScheduler` is the model-based version. Each candidate is a two-action arm, and its index is the
subsidy at which waiting becomes as good as reviewing. The index is found by binary search over the
subsidy and value iteration for the single-arm MDP.

```python
from laix import WhittleCandidate, WhittleScheduler, WhittleTransition

candidate = WhittleCandidate(
    id="refund",
    states=("bad", "good"),
    start="bad",
    active_transitions=(
        WhittleTransition(state="bad", next_state="good"),
        WhittleTransition(state="good", next_state="good"),
    ),
    passive_transitions=(
        WhittleTransition(state="bad", next_state="bad"),
        WhittleTransition(state="good", next_state="good"),
    ),
    active_reward={"bad": 1.0, "good": 0.2},
    active_cost=0.1,
    discount=0.9,
)
schedule = WhittleScheduler().schedule((candidate,), budget=1.0)
```

This is exact for the supplied finite single-arm model. The fleet policy is still an index
approximation, not a global restless-bandit optimum.

## Limits

The static scheduler is a deterministic index policy. The Whittle path is exact per arm, not for the
whole fleet.

## Examples

- Python: `examples/python/decision/decision/fleet/attention_scheduler.py`
- Python: `examples/python/decision/decision/fleet/whittle_scheduler.py`
- TypeScript: `examples/typescript/decision/decision/fleet/attention_scheduler.mts`
- TypeScript: `examples/typescript/decision/decision/fleet/whittle_scheduler.mts`

## Related

- [Single decision](01-single/README.md)
- [Sequence](02-sequence.md)
- [Algorithm directions](../../07-research/01-positioning/algorithm-directions.md)
- [Algorithm prototype results](../../07-research/02-evaluation/algorithm-prototypes.md)
