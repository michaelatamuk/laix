# Fleet attention

Fleet attention answers a different question from a single planner: many pending decisions compete for
the same humans. Which decision should receive attention now, and which should wait?

| Page | Contents |
|---|---|
| [Attention scheduler](01-attention-scheduler.md) | the AADS index policy |
| [Whittle scheduler](02-whittle.md) | the exact single-arm Whittle index |

## Limits

The static scheduler is a deterministic index policy. The Whittle path is exact per arm, not for the
whole fleet.

## Examples

- Python: `examples/python/decision/decision/fleet/attention_scheduler.py`
- Python: `examples/python/decision/decision/fleet/whittle_scheduler.py`
- TypeScript: `examples/typescript/decision/decision/fleet/attention_scheduler.mts`
- TypeScript: `examples/typescript/decision/decision/fleet/whittle_scheduler.mts`

## Related

- [Single decision](../01-single/README.md)
- [Sequence](../02-sequence/README.md)
- [Algorithm directions](../../../07-research/01-positioning/algorithm-directions.md)
- [Algorithm prototype results](../../../07-research/02-evaluation/algorithm-prototypes.md)
