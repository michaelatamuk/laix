# Support helpers

This page covers the small support types the rest of the documentation builds on: the helpers below the
decision mechanisms.

## What is here

`decision/support/` holds the shared helpers. They are small and dependency-free.

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

`DecisionPolicyError(ValueError)` is raised for an unknown policy, an invalid registration or an unsupported
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
(`0.16.0`) and the rule-set and attention-vector versions (`0.8.0`).

See [Records](../01-contract/03-records.md) for the version axes.

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
| `DecisionPolicyError` | the policy registry and normalization |
| `Verb` / `VERBS` | every decision record and policy |

## Related

- [Decision contract](../01-contract/01-decision-contract.md)
- [Records](../01-contract/03-records.md)
- [Perception](../02-domain/04-perception.md)
- [Signal attention](../04-sensing/01-signals.md)
- [Live Context](../../03-appkit/02-run/03-live-context.md)
- [Versioning](../../06-project/03-release/01-versioning.md)
