# Explain a decision

A score breakdown answers “what contributed?” Counterfactual attribution answers “what would have to
change for the decision to be different?”

| Page | Contents |
|---|---|
| [Attribution](01-attribution.md) | component-level counterfactuals |
| [Search](02-search.md) | bounded search over numeric inputs |
| [Counterfactual](03-counterfactual.md) | which candidate or verification flips a decision |

## Limits

The additive path assumes component scores. The search path is a bounded grid, not a global optimizer.

## Examples

- Python: `examples/python/decision/decision/explain/counterfactual_attribution.py`
- Python: `examples/python/decision/decision/explain/counterfactual_search.py`
- TypeScript: `examples/typescript/decision/decision/explain/counterfactual_attribution.mts`
- TypeScript: `examples/typescript/decision/decision/explain/counterfactual_search.mts`

## Related

- [Single decision](../01-single/README.md)
- [History](../04-history/README.md)
- [Algorithm directions](../../../07-research/01-positioning/algorithm-directions.md)
- [Algorithm prototype results](../../../07-research/02-evaluation/algorithm-prototypes.md)
