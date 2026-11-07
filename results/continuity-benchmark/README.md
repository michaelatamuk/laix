# Decision-continuity benchmark v0 results

12 episodes, 60 decisions. The corpus is in `benchmarks/continuity/v1/`.

| Policy | Success | Promise kept | Budget adhered | Approval correct | Continuity errors |
|---|---:|---:|---:|---:|---:|
| Reference | 100% | 100% | 100% | 100% | 0 |
| Stateless `UtilityPlanner` | 0% | 100% | 0% | 100% | 36 |
| Stateful `LiveDecisionEngine` | 100% | 100% | 100% | 100% | 0 |

The stateless planner keeps choosing the action because it cannot see that the commitment was
already fulfilled, the attention budget was spent and the receipt was pending. The stateful runtime
sees that state and moves from approval to action to verification.

This is a synthetic mechanism result, not external validation. The reference policy is hand-written
and the action space is designed. See
[docs/06-research/02-evaluation/continuity-benchmark.md](../../docs/06-research/02-evaluation/continuity-benchmark.md).

Reproduce with:

```bash
python scripts/novelty/continuity/run_continuity_bench.py
```
