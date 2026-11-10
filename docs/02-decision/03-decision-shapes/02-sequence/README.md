# Sequence planning

A `Planner` answers one live decision. A `SequencePlanner` answers a chain: one option at each step of
a known horizon, under open commitments and a shared human-attention budget.

| Class | Use |
|---|---|
| `CABBPlanner` | exact best chain for a small deterministic scenario |
| `RolloutPlanner` | good-enough chain for a larger horizon; greedy completion of each first option |
| `ReplanPlanner` | rebuild the remaining chain after an executed prefix |

| Page | Contents |
|---|---|
| [CABB](01-cabb.md) | commitment-attention branch and bound |
| [Rollout](02-rollout.md) | bounded greedy completion |
| [Replan](03-replan.md) | recovery after an executed prefix |

CABB and `plan_decisions` accept `require_verified` and `max_verification_age` (TypeScript
`maxVerificationAgeMs`). Scenario commitments owned by another party are resolved through
`CommitmentGraph` before scoring, so a stale or reported external promise blocks the option.

## Limits

CABB is exact only for a finite deterministic scenario. Rollout is approximate. Replan is a recovery
layer, not a new guarantee. An uncertain or infinite-horizon version remains research work.

## Examples

- Python: `examples/python/decision/decision/sequence/sequence_planning.py`
- TypeScript: `examples/typescript/decision/decision/sequence/sequence_planning.mts`

## Related

- [Single decision](../01-single/README.md)
- [Fleet](../03-fleet/README.md)
- [History](../04-history/README.md)
- [Algorithm directions](../../../07-research/01-positioning/algorithm-directions.md)
- [Algorithm prototype results](../../../07-research/02-evaluation/algorithm-prototypes.md)
