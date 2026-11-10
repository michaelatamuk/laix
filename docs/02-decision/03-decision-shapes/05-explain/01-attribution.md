# Counterfactual attribution

`counterfactual_attribution` reads the component scores from a `Decision` produced by the live
composite or CA-VOD planner. For every alternative it computes the smallest single-component change
that would make the alternative overtake the chosen option.

```python
from laix import CAVODPlanner, PlannerPolicy, counterfactual_attribution, decide

# request is the DecisionRequest built in the one-decision example.
decision = decide(request, policy=PlannerPolicy(CAVODPlanner(), name="ca_vod.v1"))[0]
report = counterfactual_attribution(decision)
print(report.minimal.alternative_id, report.minimal.component, report.minimal.delta)
```

The additive path is exact for the composite score.

## Related

- [Explain overview](README.md)
- [Search](02-search.md)
- [Counterfactual](03-counterfactual.md)
