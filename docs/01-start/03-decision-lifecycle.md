# Decision lifecycle

LAIX sits inside one loop:

```text
moment → attention → decision → execution → outcome → learning → next decision
```

| Stage | What happens | LAIX piece |
|---|---|---|
| **Moment** | Signals, context, situation and options arrive | `DecisionRequest` |
| **Attention** | The runtime decides what matters now | `decide_attention` |
| **Decision** | One move is chosen with reason, confidence and trail | policies, planners, `Decision` |
| **Execution** | The host acts; approval, receipts and recovery stay explicit | `ExecutionBridge`, `Saga` |
| **Outcome** | The host measures what happened | `Outcome`, stores |
| **Learning** | Rewards, calibration and causal evidence improve the next choice | `UCBBandit`, `CalibrationReport`, `CalibratedPolicy` |
| **Next decision** | The loop continues, with revisions and a timeline | `StreamSession`, `DecisionTimeline` |

The state that survives the loop is [decision continuity](../02-core/04-continuity/01-decision-continuity.md):
commitments, attention budget, approvals, revisions and outcomes.

## One pass

A task has a promise due, an irreversible action and a tight attention budget.

1. The request carries the options, the open promise, the execution facts and the budget.
2. `LiveDecisionEngine` scores each option on utility, commitment, execution risk and attention.
3. It chooses the option that keeps the promise, avoids the irreversible action and respects the
   budget. The plan carries the full breakdown.
4. The host executes it through its own skill, records the receipt and measures the outcome.
5. The next decision can use the outcome, the calibration report and the decision timeline.

## Where the host stays

The host owns the experience, data, UI, execution, storage and delivery. LAIX owns the decision and
the trail.

Runnable example: [`examples/python/09-live-loop/live_loop.py`](../../examples/python/09-live-loop/live_loop.py)
and [`examples/typescript/09-live-loop/live_loop.mts`](../../examples/typescript/09-live-loop/live_loop.mts).

## Read next

- [Core overview](../02-core/README.md)
- [App-kit building blocks](../03-appkit/00-architecture.md)
- [The decision contract](../02-core/01-contract/01-decision-contract.md)
