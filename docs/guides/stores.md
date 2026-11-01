# State and outcome stores

LAIX defines the contracts. The app or a dedicated service owns persistence.

## State store

```python
from laix import ExperienceState, StateStore

class MyStore:
    def save(self, key: str, state: ExperienceState) -> None: ...
    def load(self, key: str) -> ExperienceState | None: ...
    def delete(self, key: str) -> None: ...
```

`InMemoryStateStore` is a reference implementation for tests.

Use it for short-lived experience state: current goal, phase, beliefs, open items and expiry.
Long-lived project or user memory belongs to the app or to a manager service, not to LAIX.

## Outcome store

```python
from laix import Outcome, OutcomeStore

class MyOutcomeStore:
    def add(self, outcome: Outcome) -> Outcome: ...
    def for_decision(self, decision_id: str) -> list[Outcome]: ...
    def all(self) -> list[Outcome]: ...
    def summary(self) -> dict: ...
```

`OutcomeLedger` implements the contract in memory.

Store decision consequences, not app content:

- decision id;
- metric and before/after values;
- label: helped, neutral, hurt or unknown;
- attribution;
- evidence.

Do not store raw transcripts, images, customer data or secrets in a shared outcome store. The app
keeps the evidence; the store keeps the reference and the measurement.

Learning reads labels from these outcomes. See [`outcome-learning.md`](outcome-learning.md).
