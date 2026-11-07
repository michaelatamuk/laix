# Commitments

A commitment is a promise the task has already made. LAIX treats it as decision state, not
as a note beside the decision. An action can fulfill a promise, break one, or create a new
one, and the planner scores that effect with the rest of the decision.

## What a commitment carries

| Field | Meaning |
|---|---|
| `id` | stable identity used by options and the ledger |
| `subject` | the promised outcome |
| `due` | ISO-8601 due time, or `None` |
| `status` | `open`, `done` or `cancelled` |
| `depends_on` | commitments that must be done first |
| `priority` | importance in the range `0.0` to `1.0` |
| `payload` | host-owned detail; keep sensitive data in the host |

## The ledger

`CommitmentLedger` is the in-memory view of the open promises for one task. It can:

- add, get, complete and cancel a commitment;
- list every commitment or only the open ones;
- return the due commitments for a time;
- return the next actionable commitment, skipping blocked ones;
- report which open commitments are blocked by an unfinished dependency.

`CommitmentStore` is the persistence port. `InMemoryCommitmentStore` and
`FileCommitmentStore` are the built-in implementations. The host owns the durable store.

```python
from laix import Commitment, CommitmentLedger

ledger = CommitmentLedger(
    (
        Commitment(id="c1", subject="send the report", priority=0.8),
        Commitment(id="c2", subject="publish the summary", depends_on=("c1",)),
    )
)

print(ledger.next_actionable().id)       # c1
print([item.id for item in ledger.blocked_open()])  # ['c2']
```

## How a planner sees a commitment

An option declares its effect in `params`:

```python
params={
    "commitments": {
        "fulfills": ["c1"],
        "violates": ["c2"],
        "creates": ["c3"],
        "hard": True,
    }
}
```

- `fulfills` adds reward, scaled by priority and due time;
- `violates` subtracts reward; `hard=True` removes the option when it would break an open
  promise;
- `creates` adds the cost of taking on another promise;
- a blocked fulfillment is penalised instead of counted as kept.

The `CommitmentPlanner` keeps the ordinary utility score and adds the commitment term.
`LiveDecisionEngine` includes the same term alongside execution risk and attention.

## Where commitments live in the decision

Commitments are passed in `DecisionProblem.attributes["commitments"]`. The value can be a
`CommitmentLedger`, a tuple of `Commitment` objects, or a mapping that `Commitment.from_dict`
can read. `PlanningPolicy` can also read a ledger and act on the next actionable commitment.

## What the host owns

- the subject and the due time;
- the priority and the dependency graph;
- the durable store and retention;
- whether a commitment is done or cancelled;
- the mapping from an action to a fulfillment or violation.

LAIX owns the decision and the record. It does not send the report, publish the summary or
decide that a promise was kept; the host does that and records the outcome.

## Related

- [Decision contract](01-decision-contract.md)
- [Policies](03-policies.md) — `PlanningPolicy`
- [Planners, engines and the decision contract](06-engines.md) - `CommitmentPlanner`
- [Stores](../03-appkit/05-stores.md) — `CommitmentStore`
