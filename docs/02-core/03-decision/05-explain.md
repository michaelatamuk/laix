# Explain a decision

A score breakdown answers “what contributed?” Counterfactual attribution answers “what would have to
change for the decision to be different?”

## Counterfactual attribution

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

## Bounded search

For rule-based or planner decisions, use `counterfactual_search`. It searches a caller-supplied
decision function over bounded numeric inputs and returns the smallest weighted L1 change, up to a
configurable number of changed variables.

```python
from laix import CounterfactualVariable, counterfactual_search

report = counterfactual_search(
    lambda values: "escalate" if values["risk"] >= 0.5 else "act",
    (CounterfactualVariable("risk", 0.4, 0.2, 0.8, step=0.05),),
    max_changes=1,
)
print(report.chosen_id, report.counterfactual_id, report.changes[0].new)
```

The search is exact over the generated grid when the evaluation budget is not reached. It is not a
global optimizer for arbitrary rule systems.

## Limits

The additive path assumes component scores. The search path is a bounded grid, not a global optimizer.

## Examples

- Python: `examples/python/core/decision/explain/counterfactual_attribution.py`
- Python: `examples/python/core/decision/explain/counterfactual_search.py`
- TypeScript: `examples/typescript/core/decision/explain/counterfactual_attribution.mts`
- TypeScript: `examples/typescript/core/decision/explain/counterfactual_search.mts`

## Related

- [Single decision](01-single/README.md)
- [Algorithm directions](../../06-research/01-positioning/04-algorithm-directions.md)
- [Algorithm prototype results](../../06-research/02-evaluation/algorithm-prototypes.md)
