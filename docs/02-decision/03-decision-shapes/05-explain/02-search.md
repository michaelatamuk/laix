# Bounded search

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

## Related

- [Explain overview](README.md)
- [Attribution](01-attribution.md)
- [Counterfactual](03-counterfactual.md)
