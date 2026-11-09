# Decisions as state

A `Decision` is the result of one call. A `DecisionRequest` is the input to the next one. The two
records form the state boundary between the host and the decision layer.

## The two shapes

| Shape | Role |
|---|---|
| `DecisionRequest` | subject, time, optional situation, options, signals and attributes |
| `Decision` | verb, reason code, confidence, chosen action, approval, target and trace |
| `ExecutionReceipt` | what the host did with the decision |
| `Trace` | the ordered trail of the decision |

The full field lists are in [Decision contract](../01-contract/01-decision-contract.md).

## Status and revisions

`DECISION_STATUSES` describes where a decision is in a stream: `final`, `provisional` or
`superseded`.

A revision is a new decision with `supersedes` pointing at the decision it replaces and `revision`
incremented. The app-kit streaming layer keeps the ordered timeline; the decision layer keeps the decision
record and the trace. The host owns the durable history.

## What the decision layer owns

- The decision layer produces the decision and the trace.
- The decision layer does not store the decision.
- The host and the app kit store records, revisions and receipts.

## Related

- [Decision contract](../01-contract/01-decision-contract.md)
- [Records](../01-contract/03-records.md)
- [Commitments](02-commitments.md)
- [Outcomes](03-outcomes.md)
- [Streaming decisions](../../03-appkit/02-run/02-streaming.md)
