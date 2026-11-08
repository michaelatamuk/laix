# Stores

LAIX defines the contracts. The app owns the database.

| Word | Meaning |
|---|---|
| **State** | Short-lived state of one live experience: goal, phase, beliefs and open items. |
| **Commitment** | A promised step with a due time, status and dependencies. |
| **Outcome** | A measured result of a decision. |
| **Checkpoint** | A snapshot of a stream that can be resumed. |

## Which store

| Need | Contract | What it keeps |
|---|---|---|
| Short-lived experience state | `StateStore` | Goals, phase, beliefs, observations and history. |
| Resume a stream | `StreamCheckpointStore` | Watermark, cadence, counters, buffered decisions and traces. |
| A task's promises | `CommitmentStore` | `CommitmentLedger`: due times, status, dependencies and payload. |
| Decision consequences | `OutcomeStore` | `Outcome` records: metric, before/after, label, attribution. |

## State store

Use it for the short-lived state of one live experience: goal, phase, beliefs, open items and
expiry.

```python
from laix import ExperienceState, StateStore

class MyStore:
    def save(self, key: str, state: ExperienceState) -> None: ...
    def load(self, key: str) -> ExperienceState | None: ...
    def delete(self, key: str) -> None: ...
```

`ExperienceState` carries:

| Field | Meaning |
|---|---|
| `subject` | What the experience is about. |
| `phase` | `observe`, `decide`, `act` or another phase from the core. |
| `goals` | Goals for the experience. |
| `constraints` | Hard and soft limits. |
| `beliefs` | Beliefs keyed by proposition, with confidence and evidence. |
| `history` | Append-only events: observed, belief, phase, decision, resource plan. |
| `observations` | The observations behind the beliefs. |

`InMemoryStateStore` is an in-memory implementation. `ExperienceState.snapshot()` and
`from_snapshot()` let the app persist the state in its own format. Long-lived project or user memory
belongs in the app or a manager service.

## Stream checkpoint store

Use it to resume a `StreamSession` while the app keeps its database. The snapshot keeps the watermark,
cadence, counters, buffered decisions and traces.

```python
from laix import FileStreamCheckpointStore

store = FileStreamCheckpointStore("./checkpoints")
stream.save(store, "case-1")
stream.resume(store, "case-1")
```

`InMemoryStreamCheckpointStore` is included for tests. The host can implement
`StreamCheckpointStore` with its own storage. In TypeScript, `FileStreamCheckpointStore` takes a small
`CheckpointFiles` adapter (`join`, `read`, `write`, `remove`), so the package stays runtime-neutral.

## Commitment store

Use it for a task's promised steps. The ledger keeps due time, status, dependencies and payload.

```python
from laix import Commitment, CommitmentLedger, FileCommitmentStore

ledger = CommitmentLedger(
    (Commitment(id="a", subject="send the draft", due="2026-11-01T09:00:00+00:00"),)
)
store = FileCommitmentStore("./commitments")
store.save("task-1", ledger)
restored = store.load("task-1")
```

`InMemoryCommitmentStore` is included for tests. The host can implement `CommitmentStore` with its own
storage. The commitment model is in [Commitments](../../02-core/02-domain/02-commitments.md).

## Outcome store

Use it for decision consequences.

```python
from laix import Outcome, OutcomeStore

class MyOutcomeStore:
    def add(self, outcome: Outcome) -> Outcome: ...
    def for_decision(self, decision_id: str) -> list[Outcome]: ...
    def all(self) -> list[Outcome]: ...
    def summary(self) -> dict: ...
```

`OutcomeLedger` is an in-memory implementation. Store:

- decision id;
- metric and before/after values;
- label: helped, neutral, hurt or unknown;
- attribution;
- evidence reference.

Keep transcripts, images, customer data and secrets in the app. Learning uses outcome labels:
[outcome learning](../../02-core/02-domain/03-outcomes.md).

## TypeScript

TypeScript exports `StateStore`, `InMemoryStateStore`, `StreamCheckpointStore`,
`InMemoryStreamCheckpointStore`, `FileStreamCheckpointStore`, `CommitmentStore`,
`InMemoryCommitmentStore`, `FileCommitmentStore`, `OutcomeStore` and `OutcomeLedger`.

## Boundary

- The store contracts are ports. LAIX calls them; the host implements them.
- The host owns the database, transactions, backups and retention.
- A store key is app-defined; keep it stable across restarts.
- Do not store credentials or raw customer content in a checkpoint or a decision record.

## Related

- [Streaming](../02-run/02-streaming.md) - checkpoints and resume.
- [Decision continuity](../../02-core/03-decision/04-history.md) - what survives a decision.
- [Commitments](../../02-core/02-domain/02-commitments.md) - the ledger shape.
- [Outcome learning](../../02-core/02-domain/03-outcomes.md) - what labels are used for.
- [Deployment](../05-operate/03-deployment.md) - retention and deletion.
