# Decision continuity

A LAIX decision is one step in a sequence. The next decision sees what the last one left behind:
promises, attention budget, approvals, revisions, receipts and outcomes.

This is what makes LAIX a runtime. A classifier answers one question; a runtime carries the
consequences of the answer into the next decision.

## What carries forward

| State | Shape | Where it lives |
|---|---|---|
| Open commitments | `Commitment`, `CommitmentLedger` | core commitments, host store |
| Attention budget | `AttentionBudget` | decision attributes |
| Approval state | `Decision.requires_approval`, `DecisionRecord` | decision and audit record |
| Prior decisions and revisions | `DecisionTimeline` | app kit streaming |
| Receipts and recovery | `ExecutionBridge`, `Saga` | app kit runtime |
| Outcomes and calibration | `Outcome`, `OutcomeStore`, `CalibrationReport` | app kit and core learning |

## How state reaches the next decision

The host or app kit owns the store. The next request carries the state:

1. The previous decision may fulfill, violate or create a commitment.
2. It may spend part of a shared attention budget.
3. It may require approval or leave a receipt.
4. It may supersede an earlier decision and produce a revision.
5. Its outcome may update a calibration report.

The next `DecisionProblem` includes the commitments, budget, approvals and facts that matter. The
planner scores the current options against that state. `LiveDecisionEngine` does this for utility,
commitments, execution risk and attention in one plan.

## A sequence

| Step | Decision | State after |
|---|---|---|
| 1 | acts, creating commitment `c1` | `c1` open; budget 0.6 spent; receipt pending |
| 2 | asks because `c1` is due and the budget is low | `c1` still open; approval pending |
| 3 | verifies after execution | receipt unknown; `c1` still open |
| 4 | acts on the verified result | `c1` fulfilled; receipt recorded; outcome stored |
| 5 | the next decision | calibration and the new state are available |

The exact path depends on the policy. The point is that no step starts from zero.

## What LAIX owns

LAIX evaluates the state and returns the decision. The host and the app kit own persistence:

- the host owns the durable store and retention;
- `CommitmentStore` and `OutcomeStore` define the persistence ports;
- `DecisionTimeline` defines revision and event-time semantics;
- `DecisionRecord` defines the audit lifecycle.

The core stays stateless. Continuity comes from the state the host passes into the next request.

## Why it matters

- A one-shot classifier answers one question. LAIX carries the consequences forward.
- An orchestration framework carries state. LAIX adds decision semantics to that state.
- Glue code can copy a decision object. A coherent sequence is where the integration shows.

## Sequence-level evidence

The current 120-case corpus scores one decision at a time. The continuity claim needs an episode
benchmark: 5-20 decisions with evolving commitments, budgets, approvals, revisions and receipts.

Useful measures:

- promise keeping across the episode;
- attention budget adherence across the episode;
- revision correctness after new information;
- decision drift and stability;
- recovery after a failed or unknown execution;
- calibration over time.

The design note for this extension is in
[the benchmark page](../06-research/02-evaluation/benchmark.md).

## Related

- [Decision lifecycle](../01-start/03-decision-lifecycle.md)
- [Commitments](07-commitments.md)
- [Streaming decisions](../03-appkit/02-streaming.md)
- [Stores](../03-appkit/05-stores.md)
- [Execution and recovery](../03-appkit/04-execution.md)
