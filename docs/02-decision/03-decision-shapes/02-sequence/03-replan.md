# Replan

`ReplanPlanner` replays an executed prefix, then calls CABB on the remaining steps. It is the recovery
layer after a failure or refusal.

```python
from laix import ReplanPlanner

recovery = ReplanPlanner().replan(scenario, ("ask",))
print(recovery.actions)
```

## Related

- [Sequence overview](README.md)
- [CABB](01-cabb.md)
- [Rollout](02-rollout.md)
