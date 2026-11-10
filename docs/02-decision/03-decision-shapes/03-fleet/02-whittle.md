# Exact Whittle index

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

## Related

- [Fleet overview](README.md)
- [Attention scheduler](01-attention-scheduler.md)
