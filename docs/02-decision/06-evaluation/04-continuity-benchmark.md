# Continuity benchmark

The continuity benchmark isolates the mechanism. Each episode is five decisions. A stateless
`UtilityPlanner` sees a static option set and no episode state. A stateful `LiveCompositePlanner` sees
the open commitment, attention budget, approval state and execution receipt.

## Setup

| Role | Sees |
|---|---|
| Reference | full state; hand-written ground truth |
| Stateless `UtilityPlanner` | a static option set only |
| Stateful `LiveCompositePlanner` | commitments, budget, approvals and receipts in `PlannerInput.attributes` |

The host asks for approval when the planner result sets `requires_approval`.

## Result

| DecisionPolicy | Episode success | Promise kept | Budget adhered | Approval correct | Continuity errors |
|---|---:|---:|---:|---:|---:|
| Reference | 100% | 100% | 100% | 100% | 0 |
| Stateless `UtilityPlanner` | 0% | 100% | 0% | 100% | 36 |
| Stateful `LiveCompositePlanner` | 100% | 100% | 100% | 100% | 0 |

The corpus has 12 episodes and 60 decisions. The stateful policy completes every episode. The
stateless policy repeats actions because it cannot see that the commitment was fulfilled, the
attention budget was spent and the receipt was pending.

## What it shows

- The stateful policy uses the supplied state to move from approval to action to verification.
- The stateless policy repeats actions and exhausts the budget.
- The difference is the state, not a different chooser.

## Scope

The benchmark is a synthetic mechanism test with a designed action space. It shows that the stateful loop
uses the supplied state. The corpus and result are in
[`benchmarks/continuity/v1/`](../../../benchmarks/continuity/v1/README.md) and
[`results/continuity-benchmark/`](../../../results/continuity-benchmark/README.md). The design note is
[the continuity benchmark page](../../07-research/02-evaluation/continuity-benchmark.md).

## Related

- [Decision continuity](../03-decision-shapes/04-history/README.md)
- [Outcomes](../02-domain/03-outcomes.md)
- [Evaluation](01-cases.md)
