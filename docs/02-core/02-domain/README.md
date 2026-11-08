# Domain

The domain layer holds the records and state the decision layer reads and writes. It has no planner and
no policy.

| Page | Contents |
|---|---|
| [Decisions](01-decisions.md) | `DecisionRequest`, `Decision`, status, revisions and trail |
| [Commitments](02-commitments.md) | promises, due times, dependencies and stores |
| [Outcomes](03-outcomes.md) | measured outcomes, labels, ledger and store |
| [Perception](04-perception.md) | detections, detector contract and frames |

The public shapes are described in [Decision contract](../01-contract/01-decision-contract.md). This
chapter explains what the records mean and how they carry from one decision to the next.
