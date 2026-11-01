# State and outcome stores

LAIX defines the contracts. The app or a dedicated service owns persistence.

## State store

Use it for short-lived experience state: current goal, phase, beliefs, open items and expiry.

```python
from laix import ExperienceState, StateStore

class MyStore:
    def save(self, key: str, state: ExperienceState) -> None: ...
    def load(self, key: str) -> ExperienceState | None: ...
    def delete(self, key: str) -> None: ...
```

`InMemoryStateStore` is a reference implementation for tests.

Long-lived project or user memory belongs to the app or to a manager service. `ExperienceState`
supports `snapshot()` and `from_snapshot()` when the app wants to persist it in its own database.

## Outcome store

Use it for decision consequences, not app content.

```python
from laix import Outcome, OutcomeStore

class MyOutcomeStore:
    def add(self, outcome: Outcome) -> Outcome: ...
    def for_decision(self, decision_id: str) -> list[Outcome]: ...
    def all(self) -> list[Outcome]: ...
    def summary(self) -> dict: ...
```

`OutcomeLedger` implements the contract in memory.

Keep these fields:

- decision id;
- metric and before/after values;
- label: helped, neutral, hurt or unknown;
- attribution;
- evidence reference.

Transcripts, images, customer data and secrets stay in the app. A shared outcome store keeps the
reference and the measurement.

## TypeScript

The TypeScript package mirrors the contracts with `StateStore`, `InMemoryStateStore`, `OutcomeStore`
and `OutcomeLedger`.

## Learning

Learning reads labels from the outcome store. See [outcome learning](outcome-learning.md).
