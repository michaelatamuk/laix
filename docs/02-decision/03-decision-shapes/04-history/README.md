# Decision history

A LAIX decision is one step in a sequence. The next decision sees what the previous one left behind:
promises, human-attention budget, approvals, revisions, receipts and outcomes.

| Page | Contents |
|---|---|
| [Continuity](01-continuity.md) | what carries forward and how state reaches the next decision |
| [Repair](02-repair.md) | CDR: continuity decision repair |
| [Revalidation](03-revalidation.md) | hold, revise or escalate an earlier decision |

## Limits

The exact repair is a minimum-weight vertex cover over small histories. Large histories use the greedy
path. The full method remains incremental truth maintenance with a weighted MaxSAT repair.

## Examples

- Python: `examples/python/decision/decision/history/continuity_repair.py`
- Python: `examples/python/decision/decision/history/continuity_repair_exact.py`
- Python: `examples/python/decision/decision/history/conflict_scenario.py`
- TypeScript: `examples/typescript/decision/decision/history/continuity_repair.mts`
- TypeScript: `examples/typescript/decision/decision/history/continuity_repair_exact.mts`

## Related

- [Single decision](../01-single/README.md)
- [Sequence](../02-sequence/README.md)
- [Fleet](../03-fleet/README.md)
- [Explain](../05-explain/README.md)
- [Commitments](../../02-domain/02-commitments.md)
- [Continuity benchmark](../../06-evaluation/04-continuity-benchmark.md)
