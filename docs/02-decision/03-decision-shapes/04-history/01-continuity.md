# Continuity

Decision continuity is the property that each step starts from the current state instead of from zero.
This is what makes LAIX stateful rather than a one-shot classifier. The decision layer stays stateless;
the host passes the current state into the next request.

## What carries forward

| State | Shape | Where it lives |
|---|---|---|
| Open commitments | `Commitment`, `CommitmentLedger` | decision domain commitments and the host store |
| Human-attention budget | `HumanAttentionBudget` | decision attributes |
| Approval state | `Decision.requires_approval`, `DecisionRecord` | the decision and the audit record |
| Prior decisions and revisions | `DecisionTimeline` | app-kit streaming |
| Receipts and recovery | `ExecutionBridge`, `Saga` | app kit |
| Outcomes and calibration | `Outcome`, `OutcomeStore`, `CalibrationReport` | decision domain outcomes and host stores |

Outcomes and calibration are described in [Outcomes](../../02-domain/03-outcomes.md) and
[Learning](../../05-learning/README.md).

## How state reaches the next decision

```mermaid
sequenceDiagram
    participant Host
    participant Decision
    participant Store
    Host->>Decision: DecisionRequest with current state
    Decision-->>Host: Decision
    Host->>Store: save commitments, budget and approval
    Host->>Host: execute the chosen action
    Host->>Store: save receipt and outcome
    Store-->>Host: state for the next request
    Host->>Decision: next DecisionRequest with updated state
```

1. The previous decision may fulfill, violate or create a commitment.
2. It may spend part of a shared human-attention budget.
3. It may require approval or leave an execution receipt.
4. It may supersede an earlier decision and produce a revision.
5. Its outcome may update a calibration report or a learner.

The next `DecisionRequest` carries the commitments, budget, approvals and receipts that matter. The
planner receives them in `PlannerInput.attributes` and scores the current options against that
state. `LiveCompositePlanner` does this for utility, commitments, execution risk and attention in one
planner result.

## A sequence

| Step | Decision | State after |
|---|---|---|
| 1 | acts and creates commitment `c1` | `c1` open; budget 0.6 spent; receipt pending |
| 2 | asks because `c1` is due and the budget is low | `c1` open; approval pending |
| 3 | verifies after execution | receipt unknown; `c1` still open |
| 4 | acts on the verified result | `c1` fulfilled; receipt recorded; outcome stored |
| 5 | the next decision | calibration and the new state are available |

The exact path depends on the policy. The invariant is that no step starts from zero.

## Why it matters

The [continuity benchmark](../../06-evaluation/04-continuity-benchmark.md) measures the mechanism: 12
episodes, 60 decisions, a stateless planner and a stateful composite planner.

- A one-shot classifier answers one question. LAIX carries the consequences into the next decision.
- An orchestration framework carries state. LAIX adds decision semantics to that state.
- Glue code can copy a decision object. A coherent sequence is where the integration shows.

## Related

- [History overview](README.md)
- [Repair](02-repair.md)
- [Revalidation](03-revalidation.md)
- [Commitments](../../02-domain/02-commitments.md)
- [Planners](../01-single/01-planners.md#human-attention-planner)
- [Streaming decisions](../../../03-appkit/02-run/02-streaming.md)
- [Stores](../../../03-appkit/04-connect/01-stores.md)
- [Execution and recovery](../../../03-appkit/03-execute/01-execution-and-recovery.md)
