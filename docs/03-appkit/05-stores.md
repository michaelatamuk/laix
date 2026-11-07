# Stores

LAIX defines the contracts. The app owns the database.

| Word | Meaning |
|---|---|
| **State** | Short-lived state of one live experience: goal, phase, beliefs and open items. |
| **Commitment** | A promised step with a due time, status and dependencies. |
| **Outcome** | A measured result of a decision. |

## State store

Use it for the short-lived state of one live experience: goal, phase, beliefs, open items, expiry.

```python
from laix import ExperienceState, StateStore

class MyStore:
    def save(self, key: str, state: ExperienceState) -> None: ...
    def load(self, key: str) -> ExperienceState | None: ...
    def delete(self, key: str) -> None: ...
```

`InMemoryStateStore` is an in-memory implementation.

`ExperienceState` has `snapshot()` and `from_snapshot()` for app-owned persistence. Long-lived project
or user memory belongs in the app or a manager service.

## Stream checkpoint store

Use it to resume a `StreamSession` while the app keeps its database. The snapshot keeps the watermark,
cadence, counters, buffered decisions and traces.

```python
from laix import FileStreamCheckpointStore

store = FileStreamCheckpointStore("./checkpoints")
stream.save(store, "case-1")
stream.resume(store, "case-1")
```

`InMemoryStreamCheckpointStore` is included for tests. The host can implement `StreamCheckpointStore`
with its own storage.

In TypeScript, `FileStreamCheckpointStore` takes a small `CheckpointFiles` adapter
(`join`, `read`, `write`, `remove`), so the package stays runtime-neutral. A Node host can pass
`node:fs` and `node:path` wrappers.

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

`InMemoryCommitmentStore` is included for tests. The host can implement `CommitmentStore` with its
own storage.

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

`OutcomeLedger` is an in-memory implementation.

Store:

- decision id;
- metric and before/after values;
- label: helped, neutral, hurt or unknown;
- attribution;
- evidence reference.

Keep transcripts, images, customer data and secrets in the app.

TypeScript exports `StateStore`, `InMemoryStateStore`, `StreamCheckpointStore`,
`InMemoryStreamCheckpointStore`, `FileStreamCheckpointStore`, `CommitmentStore`,
`InMemoryCommitmentStore`, `FileCommitmentStore`, `OutcomeStore` and `OutcomeLedger`.

Learning uses outcome labels: [outcome learning](../02-core/05-learning/01-outcome-learning.md).
