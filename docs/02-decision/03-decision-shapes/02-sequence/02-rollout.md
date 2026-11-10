# Rollout

`RolloutPlanner` uses CABB's evaluator for each option at the current step and completes the rest
greedily. It is bounded by the horizon and is not exact.

```python
from laix import RolloutPlanner

approximate = RolloutPlanner().plan(scenario)
print(approximate.actions)
```

## Related

- [Sequence overview](README.md)
- [CABB](01-cabb.md)
- [Replan](03-replan.md)
