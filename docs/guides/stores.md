# Stores

LAIX defines the contracts. The app owns the database.

| Word | Meaning |
|---|---|
| **State** | Short-lived experience data: goal, phase, beliefs and open items. |
| **Outcome** | A measured result of a decision. |

## State store

Use it for short-lived experience state: goal, phase, beliefs, open items, expiry.

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

TypeScript exports `StateStore`, `InMemoryStateStore`, `OutcomeStore` and `OutcomeLedger`.

Learning uses outcome labels: [outcome learning](outcome-learning.md).
