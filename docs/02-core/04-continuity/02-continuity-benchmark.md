# Continuity benchmark

The continuity benchmark isolates the mechanism. Each episode is five decisions. A stateless
`UtilityPlanner` sees a static option set and no episode state. A stateful `LiveDecisionEngine` sees
the open commitment, attention budget, approval state and execution receipt.

## Setup

| Role | Sees |
|---|---|
| Reference | full state; hand-written ground truth |
| Stateless `UtilityPlanner` | a static option set only |
| Stateful `LiveDecisionEngine` | commitments, budget, approvals and receipts in `DecisionProblem.attributes` |

The host asks for approval when the plan sets `requires_approval`.

## Result

| Policy | Episode success | Promise kept | Budget adhered | Approval correct | Continuity errors |
|---|---:|---:|---:|---:|---:|
| Reference | 100% | 100% | 100% | 100% | 0 |
| Stateless `UtilityPlanner` | 0% | 100% | 0% | 100% | 36 |
| Stateful `LiveDecisionEngine` | 100% | 100% | 100% | 100% | 0 |

The corpus has 12 episodes and 60 decisions. The stateful policy completes every episode. The
stateless policy repeats actions because it cannot see that the commitment was fulfilled, the
attention budget was spent and the receipt was pending.

## What it shows

- The stateful policy uses the supplied state to move from approval to action to verification.
- The stateless policy repeats actions and exhausts the budget.
- The difference is the state, not a different chooser.

## Scope

The benchmark is a synthetic mechanism test with a designed action space. It shows that the runtime
uses the supplied state. The corpus and result are in
[`benchmarks/continuity/v1/`](../../../benchmarks/continuity/v1/README.md) and
[`results/continuity-benchmark/`](../../../results/continuity-benchmark/README.md). The design note is
[the continuity benchmark page](../../06-research/02-evaluation/continuity-benchmark.md).

## Related

- [Decision continuity](01-decision-continuity.md)
- [Outcome learning](../05-learning/01-outcome-learning.md)
- [Evaluation](../06-reference/01-evaluation.md)
