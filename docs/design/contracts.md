# LAIX contracts — v1.0

**Schema version:** `1.1`
**Policy version:** `2026.1`
**Normative shape:** [`../../packages/python/laix/src/laix/schemas/laix-v1.schema.json`](../../packages/python/laix/src/laix/schemas/laix-v1.schema.json)

The generated schema defines the shape of every contract. `schema.py` builds it from the dataclasses
in `contracts.py` and writes the committed file:

```powershell
py -c "from laix.schema import write_schema; write_schema()"
```

The staleness test regenerates the document and fails when the committed file differs:

```powershell
py -m pytest tests/test_laix.py -k schema
```

The policy rules live in `policies/action.py` and `README.md`. Thresholds, rule order and the seven verbs are
part of the policy version.

## The ten contracts

| # | Contract | Version field | Purpose |
|---|---|---|---|
| 1 | `Observation` | `schema_version` | one measurement, source, confidence, cost and latency |
| 2 | `Belief` | `schema_version` | a proposition with confidence, evidence and expiry |
| 3 | `Goal` | `schema_version` | what the experience improves, its priority, metric and deadline |
| 4 | `Constraint` | `schema_version` | latency, cost, risk, interruption, approval or safety limit |
| 5 | `Action` | `schema_version` | a candidate verb with benefit, cost, risk, reversibility and approval need |
| 6 | `Situation` | `schema_version` | observations, beliefs, goals, constraints, phase and horizon |
| 7 | `Decision` | `schema_version` | chosen verb, action, rationale, alternatives and approval flag |
| 8 | `Outcome` | `schema_version` | measured metric, before/after, direction, attribution and label |
| 9 | `Receipt` | `schema_version` | executed, refused, cancelled, failed or undone execution record |
| 10 | `Trace` | `schema_version` | ordered evidence for one decision |

Every record carries `schema_version = "1.1"`, so a future change is detected and migrated.

## Version 1.1

- Public type names and contract field names.
- The seven verbs: `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate`.
- Approval is a boolean on the decision; `ask` stays for questions and requests.
- JSON Schema shape and version.
- Policy rule order and thresholds.

A contract change creates a new schema version. Version 1 stays available for existing callers.
