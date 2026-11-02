# Records

## What a record is

A record is a named data shape. It says which fields exist, what type they have and what values are
allowed. LAIX uses records for requests, decisions, outcomes and the lifecycle around them.

The Decision response itself is documented in [The Decision response](01-decisions.md). This page
covers the other core records, the `DecisionRecord` lifecycle and the schema.

| Word | Meaning |
|---|---|
| **Record** | One data object, such as a decision or an outcome. |
| **Schema** | A machine-readable description of a record. |
| **Vector** | A fixed input and its expected output, used as a test case. |

Two versions travel with a decision, and they mean different things:

- `schema_version` is the version of the record shape.
- `policy_version` is the version of the rule set that produced the decision.

## The core records

### Request records

| Record | Carries |
|---|---|
| `DecisionRequest` | subject, moment, signals, context, situation, options, attributes and confidence |
| `Signal` | id, kind, title, detail, severity, confidence, due, evidence refs and interruption cost |
| `Context` | time, quiet hours, thresholds, budget, feedback and escalation |
| `Feedback` | state, time, until and note |
| `Observation` | source, kind, confidence, payload, cost and latency |
| `Belief` | proposition, confidence, evidence, update time and expiry |
| `Goal` | statement, priority, metric, target and deadline |
| `Constraint` | kind, value, hard flag and statement |
| `ActionOption` | id, verb, name, benefit, cost, risk, reversibility and approval |
| `Situation` | observations, beliefs, goals, constraints, phase, horizon and attributes |

### Response records

`Decision`, `EvidenceRef`, `Intent` and `ScoreBreakdown` are documented in
[The Decision response](01-decisions.md).

### Outcome and execution records

| Record | Carries |
|---|---|
| `Outcome` | decision id, metric, before/after, direction, attribution and label |
| `ExecutionReceipt` | chosen option, status, actor, result and error |
| `Trace` | ordered events for one decision |

Every core record carries `schema_version`.

## DecisionRecord lifecycle

The core Decision response is immutable. The app kit wraps it in a `DecisionRecord`, with `Approval`,
`Undo` and `AuditEvent`, for approval, execution and undo.

```text
draft -> approved -> executed -> undone
  |
  +-> rejected
```

`executed True` means the record ran and its fingerprint still matches.

## JSON

Python records have `to_dict()` and use snake_case. The JSON Schema uses the same names. TypeScript
uses camelCase properties for the same concepts.

## Generate the schema

From `packages/python/laix`:

```powershell
py -c "from laix.core.schema import write_schema; write_schema()"
```

Check that the committed file is current:

```powershell
py -m pytest tests/test_laix.py -k schema
```

## Versions

| Thing | Version |
|---|---|
| Package | `0.8.1` |
| Record schema | `0.8.0` |
| Rule sets | `0.8.0` |
| Attention vectors | `0.8.0` |

The package, the schema and the rule sets move separately. A record-shape change bumps the schema; a
rule or threshold change bumps the rule set.

## Change rules

1. Change a record shape → bump the schema version and regenerate the schema.
2. Change a rule or threshold → bump the rule-set version.
3. Change a vector or weight → bump the vector version.
4. Add a decision class → add a rule set with a name and version. The decision shape stays the same.

The seven verbs are part of the contract: `wait`, `observe`, `guide`, `ask`, `act`, `verify`,
`escalate`.

## Files

| File | Contents |
|---|---|
| `packages/python/laix/src/laix/core/schema/laix-v1.schema.json` | generated schema for all core records, including `Decision` |
| `packages/contracts/decision-record.v1.schema.json` | `DecisionRecord` shape |
| `packages/contracts/attention.v1.json` | attention test cases |
| `packages/contracts/attention-bench.v1.json` | attention outcome cases |

The schema is generated from the Python records, so it is the only decision schema. The test
vectors are hand-written and shared by both packages.
