# Outcomes

An outcome is the measured result of a decision. It is a record, not a learner. The learning pages turn
outcomes into rewards and better choices.

```text
decision → outcome → reward → learner → next decision
```

The app measures the outcome. LAIX owns the record shape, the ledger and the store port.

## Outcome

`Outcome` is the measured result of one decision:

| Field | Meaning |
|---|---|
| `id` | Outcome id. |
| `decision_id` | The decision that produced it. |
| `metric` | The measured quantity. |
| `before`, `after` | The values before and after the decision. |
| `delta` | `after - before`. |
| `label` | `helped`, `neutral`, `hurt` or `unknown`. |
| `direction` | `higher-better` or `lower-better`. |
| `attributed` | Whether the outcome is attributed to the decision. |
| `evidence` | Host-owned detail. |
| `measured_at` | When the outcome was measured. |
| `note` | Host note. |
| `schema_version` | The record version. |

`Outcome.__post_init__` rejects an unknown label or direction. `to_dict()` serialises it.

## Outcome ledger

`OutcomeLedger` is the in-memory store. Its main method records a measurement and derives the label:

```python
from laix import OutcomeLedger

ledger = OutcomeLedger()
outcome = ledger.record(
    "DEC-1",
    metric="resolution_time",
    before=120.0,
    after=90.0,
    direction="lower-better",
    attributed=True,
)
print(outcome.label)  # helped
```

The label rule:

```text
gain = delta        if direction == "higher-better"
       -delta       if direction == "lower-better"

gain > tolerance      -> helped
gain < -tolerance     -> hurt
otherwise             -> neutral
```

`tolerance` defaults to `1e-9`. An explicit `label` overrides the derived value.

| Method | Result |
|---|---|
| `record(decision_id, ...)` | Builds, stores and returns one `Outcome`. |
| `add(outcome)` | Stores an existing outcome. |
| `for_decision(decision_id)` | The outcomes for one decision. |
| `all()` | Every outcome. |
| `extend(outcomes)` | Adds several outcomes. |
| `summary()` | `measured`, `attributed`, `attributionCoverage`, `helped`, `neutral`, `hurt`, `meanGain`, `precision`. |
| `by_metric()` | Per metric: `measured`, `attributed`, `helped`, `hurt`, `gain`. |
| `to_dict()` | `tolerance`, `records`, `summary`. |

`OutcomeStore` is the persistence port: `add`, `for_decision`, `all`, `summary`. The host implements
it with its own database.

## Signal-attention outcomes

Signal attention has its own outcome shapes:

- `SignalAttentionOutcome` carries `signal_id`, `kind`, `verb`, `result`, `reason_code`, `score` and `at`.
- `SignalAttentionLog` keeps the latest `limit` records (default 500) and reports `total`, `precision`,
  `hazard_rate`, `adjustment`, `calibration` and `by_kind`.
- `labels.py` maps a feedback state and reason to a result: `accepted`/`confirmed`/`signed` → `helped`;
  `wrong`/`false_alarm` → `hurt`; `dismissed`/`snoozed`/`assigned` → a reason-based neutral or hurt;
  otherwise `unknown`.

`SignalAttentionLog.adjustment(kind, weight=12.0)` returns a per-kind point adjustment. A host can place it
in `SignalContext.learned` so the next signal decision uses it.

## What the app owns

The app owns the metric, the measurement, the decision-to-arm map and the feedback state. LAIX owns the
record shape, the ledger and the store port.

## Related

- [Rewards and bandit](../05-learning/03-bandit.md)
- [Causal attribution](../05-learning/04-causal.md)
- [Calibration](../05-learning/01-calibration.md)
- [Stores](../../03-appkit/04-connect/01-stores.md) — `OutcomeStore`
