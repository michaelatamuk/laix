# Decision lifecycle

LAIX sits inside one loop:

```text
moment -> attention -> decision -> execution -> outcome -> learning -> next decision
```

| Stage | What happens | LAIX piece | Owner |
|---|---|---|---|
| **Moment** | Signals, context, situation and options arrive. | `DecisionRequest` | Host |
| **Attention** | The runtime decides what matters now. | `decide_signal_attention` | LAIX |
| **Decision** | One move is chosen with a reason, confidence and trail. | policies, planners, `Decision` | LAIX |
| **Execution** | The host acts; approval, receipts and recovery stay explicit. | `ExecutionBridge`, `Saga` | Host, with the app kit if chosen |
| **Outcome** | The host measures what happened. | `Outcome`, stores | Host |
| **Learning** | Rewards, calibration and causal evidence improve the next choice. | `UCBBandit`, `CalibrationReport`, `CalibratedPolicy` | Host, with LAIX primitives |
| **Next decision** | The loop continues with revisions and a timeline. | `StreamSession`, `DecisionTimeline` | Host, with the app kit if chosen |

The core is stateless. The host passes the current state into each request.

## One pass

A task has a promise due, an irreversible action and a tight attention budget.

1. The request carries the options, the open promise, the execution facts and the budget.
2. `LiveCompositePlanner` scores each option on utility, commitment, execution risk and attention.
3. It chooses the option that keeps the promise, avoids the irreversible action and respects the
   budget. The planner result carries the full breakdown.
4. The host executes it through its own skill, records the receipt and measures the outcome.
5. The next decision can use the outcome, the calibration report and the decision timeline.

The decision is not the end of the story. It is the input to the next one.

## What survives

| State | Why it matters | Where it lives |
|---|---|---|
| Open commitments | The next decision must not break a promise. | Core commitments and the host store. |
| Attention budget | Human interruption is finite. | Decision attributes. |
| Approval state | A pending approval is not an approval. | Decision and record. |
| Prior decisions and revisions | A later decision may supersede an earlier one. | Decision timeline. |
| Receipts and recovery | An unknown outcome must be reconciled, not retried blindly. | Execution bridge and saga. |
| Outcomes and calibration | The next choice can learn from the last one. | Outcome store and calibration report. |

That hand-off is [decision continuity](../../02-core/04-continuity/01-decision-continuity.md).

## One-shot or loop

| You have | Use |
|---|---|
| One request and one answer | `decide` or `DecisionClient.decide` |
| A stream of events over time | `StreamSession` |
| A decision that changes the world | `ExecutionBridge` |
| State that must survive a restart | `StateStore` and `StreamCheckpointStore` |

A one-shot call is a valid use of LAIX. The loop is what makes it a runtime: the same chooser sees a
different, current state on every step.

## Where the host stays

The host owns the experience, data, UI, execution, storage and delivery. LAIX owns the decision and
the trail.

- The host decides when to call LAIX.
- The host owns the domain nouns and the execution handlers.
- The host owns the database and the retention policy.
- LAIX returns the decision; the host decides what to do with it.

The boundary is described in [Scope and boundaries](../../04-concepts/01-architecture/02-scope-and-boundaries.md).

## Runnable example

[`examples/python/09-live-loop/live_loop.py`](../../../examples/python/09-live-loop/live_loop.py) and
[`examples/typescript/09-live-loop/live_loop.mts`](../../../examples/typescript/09-live-loop/live_loop.mts)
run one full loop: stream, decision, execution, outcome, calibration and timeline.

## Read next

- [Core overview](../../02-core/README.md) - the contract and the mechanisms.
- [App-kit overview](../../03-appkit/README.md) - the optional runtime.
- [Streaming](../../03-appkit/02-run/02-streaming.md) - decisions over event time.
- [Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md) - the write boundary.
- [Stores](../../03-appkit/04-connect/01-stores.md) - what the host persists.
- [The decision contract](../../02-core/01-contract/01-decision-contract.md) - every field.
