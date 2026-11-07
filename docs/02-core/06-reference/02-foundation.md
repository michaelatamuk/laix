# Foundation: perception and support

This page covers the small core types the rest of the documentation builds on: the records and
helpers below the decision mechanisms.

## Perception

Core defines the perception records and the detector contract. The runtime loop lives in the app
kit.

| Type | Fields |
|---|---|
| `Detection` | `id`, `detector`, `kind`, `subject`, `at`, `confidence`, `severity`, `payload` |
| `PerceptionEvent` | `subject`, `at`, `payload` |
| `PerceptionFrame` | `subject`, `at`, `detections`, `allowed`, `skipped`, `uncertainty`, `deep_calls`, `cost` |

`Detection.confidence` is clamped to `0..1`. `Detection.severity` uses the same severity words as
signal attention: `critical`, `high`, `medium`, `low` or `info`.

`Detector` is a protocol:

```python
class Detector(Protocol):
    name: str
    tier: str
    cost: float
    latency_ms: int
    information_gain: float

    def detect(self, event: PerceptionEvent) -> Iterable[Detection]: ...
```

`PerceptionFrame.to_dict()` uses `subject`, `at`, `detections`, `allowed`, `skipped`, `uncertainty`,
`deepCalls` and `cost`. It is the frame a detector loop returns after admission.

The app-kit runtime that drives detectors is `LiveContext` with `CallableDetector`. It lives in
`appkit/live_context/`. See [Live Context](../../03-appkit/03-live-context.md).

## Support

`core/support/` holds the shared helpers. They are small and dependency-free.

### Identity

| Helper | Result |
|---|---|
| `new_id(prefix)` | `<PREFIX>-<10 uppercase hex>` |
| `new_execution_receipt_id()` | a new receipt id with the `RCT` prefix |

### Time

| Helper | Result |
|---|---|
| `utcnow()` | the current timezone-aware UTC datetime |
| `iso(value=None)` | an ISO-8601 UTC string with seconds precision |
| `parse_iso(value)` | a UTC datetime, or `None` for an empty or unparsable value |

`parse_iso` attaches UTC to a naive datetime and converts an aware datetime to UTC.

### Values

| Helper | Result |
|---|---|
| `clamp(value, low=0.0, high=1.0)` | the value limited to the range |
| `confidence_band(value)` | `high` at `>= 0.8`, `medium` at `>= 0.55`, otherwise `low` |

### Serialization

| Helper | Result |
|---|---|
| `to_primitive(value)` | dataclasses, dicts, lists and tuples converted recursively |
| `to_string_tuple(value)` | `None` → `()`, a string → `(value,)`, otherwise a tuple of strings |

`to_primitive` is the base of the record `to_dict()` methods and depends only on the standard library.

### Errors

`PolicyError(ValueError)` is raised for an unknown policy, an invalid registration or an unsupported
policy result.

### Verbs

`Verb` is a string enum. `VERBS` is the tuple in declaration order:

```text
wait, observe, guide, ask, act, verify, escalate
```

`Decision`, `ActionOption`, `Signal` and every policy use the same set. An unknown verb raises
`ValueError` when a record is built.

### Version

`SCHEMA_VERSION = "0.8.0"` is the record-shape version. It is separate from the package version
(`0.10.0`) and the rule-set and attention-vector versions (`0.8.0`).

See [Records and schema](../01-contract/02-records-and-schema.md) for the version axes.

## Where the helpers are used

| Helper | Used by |
|---|---|
| `new_id` | `decide`, records and execution receipts |
| `iso` | decision timestamps, traces and receipts |
| `parse_iso` | commitments, planners and calibration reports |
| `clamp` | confidence, risk, benefit, interruption and priorities |
| `confidence_band` | belief confidence and calibration views |
| `to_primitive` | record serialization |
| `to_string_tuple` | evidence, recipients and dependency ids |
| `PolicyError` | the policy registry and normalization |
| `Verb` / `VERBS` | every decision record and policy |

## Related

- [Decision contract](../01-contract/01-decision-contract.md)
- [Records and schema](../01-contract/02-records-and-schema.md)
- [Signal attention](../02-decide/01-signal-attention.md)
- [Live Context](../../03-appkit/03-live-context.md)
- [Versioning](../../05-project/versioning.md)
