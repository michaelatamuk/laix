# The decision contract

The contract has two sides:

- the app sends a **request** — what is happening and what it can do;
- LAIX returns a **response** — one verb, a reason, and optional execution details.

Records hold the request, the response and the lifecycle around them.

## The request

A request is a `DecisionRequest`. It carries either:

- `signals` and `context` for attention; or
- `situation` and `options` for an action decision.

### Terms

| Term | Meaning |
|---|---|
| **Request** | What the app sends to LAIX: what is happening and what it can do. |
| **Signal** | One item that might need attention, such as a deadline or a risk. |
| **Context** | Rules around attention: current time, quiet hours, minimum severity. |
| **Option** | One thing the app can do. |

### Example

A bill is due tomorrow. The app sends one signal and the attention context.

```python
from datetime import datetime, timezone

from laix import Context, DecisionRequest, Signal

DecisionRequest(
    subject="electricity bill",
    at="2026-11-01T10:00:00+00:00",
    signals=(Signal(
        id="bill-1",
        kind="deadline",
        title="Electricity bill due tomorrow",
        severity="high",
        confidence=0.95,
        due="2026-11-02T09:00:00+00:00",
    ),),
    context=Context(
        now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
        quiet_hours=("22:00", "06:00"),
        min_severity="medium",
    ),
)
```

A request also accepts `event_id` for stream dedupe, `target` and `recipients` for
a group decision, plus `deadline` and `valid_until`. A one-shot decision may leave
them empty; a stream session copies the deadline and validity onto the response.

## The response

The response is a `Decision`; it lives under `core/decisions/response/`.

### Terms

| Term | Meaning |
|---|---|
| **Decision response** (`Decision`) | What LAIX sends back: one verb, a reason, and optional execution details. |
| **Verb** | The word that says what to do next. |
| **Reason code** | A short stable label for the rule that fired. |
| **Chosen option id** (`action_id`) | The id of the chosen option, if there is one. |
| **Confidence** | How sure the rule set is, from `0` to `1`. |
| **Rule-set version** (`policy_version`) | Which version of the rule set produced the response. |

### Example

LAIX returns:

```text
guide worth_surfacing 84.0
```

| Field | Value | Meaning |
|---|---|---|
| `verb` | `guide` | Show the bill now; the user decides when to pay. |
| `reason_code` | `worth_surfacing` | The attention rules say it is worth showing. |
| `score` | `84.0` | The rule set's ranking. |
| `confidence` | `0.95` | How sure the rule set is. |
| `requires_approval` | `false` | Runs without approval. |
| `deliver` | `true` | Show it now. |
| `record` | `true` | Keep it in history. |

## The response fields

| Field | Meaning |
|---|---|
| `verb` | What to do next. |
| `confidence` | How sure the rule set is, `0..1`. |
| `reason_code` | The rule that fired. Use this in app logic. |
| `rationale` | Explanation for people. Use `reason_code` in app logic. |
| `action_id` | The chosen option id, if there is one. |
| `intent` | `{capability, args}` the app can execute; for a handover, `Intent("handover", {"target", "reason"})`. |
| `requires_approval` | Ask a person before executing. |
| `reversible` | Whether the chosen option can be undone. |
| `undo_hint` | How to undo it. |
| `score` | Ranking inside one rule set. Use `confidence` for probability. |
| `breakdown` | Score parts for the decision. |
| `cost_of_waiting` | Cost of waiting in this situation. |
| `evidence` | References that support the decision. |
| `decision_id` | Id for records and outcomes. |
| `situation_id` | The id of the situation this decision answered, when there is one. |
| `attributes` | Values the rule set used to reach the decision. |
| `policy_version` | Which version of the rule set produced it. |
| `trace_id` | Correlates related events for this decision. |
| `deliver` | Show now. |
| `record` | Keep it. |
| `created_at` | When it was made. |
| `confidence_source` | Where the confidence came from. |
| `calibrated` | Whether the confidence is a calibrated probability. |
| `alternatives` | Other options, their score and why they lost. |
| `constraints_applied` | Hard limits that changed the option set. |
| `stream_id` | The stream session that produced it; empty for a one-shot decision. |
| `event_time` | When the event happened. |
| `deadline` | When the decision had to be made. |
| `valid_until` | How long the decision applies. |
| `supersedes` | The decision this one replaces. |
| `revision` | `0` for the first decision, then `1`, `2`, … |
| `status` | `final`, `provisional` or `superseded`. |
| `target` | `one`, `some`, `all`, `peer` or `gather`. |
| `recipients` | The user or group ids that receive the decision. |

## The seven verbs

| Verb | Meaning |
|---|---|
| `wait` | Hold for now; keep watching. |
| `observe` | Get more information first. |
| `guide` | Show the situation to a person. |
| `ask` | Ask a person or agent for information or a decision. |
| `act` | Run the chosen option now. |
| `verify` | Check whether an earlier step worked. |
| `escalate` | Hand over to someone with more authority. |

A notification is a `guide` decision plus an app delivery channel. Approval is the
`requires_approval` flag.

## More examples

**Quiet hours.** The same bill at 23:30 returns `wait quiet_hours 84.0`. The score is still high, but
`deliver` is `false` and `record` is `true`.

**Look first.** A late parcel with a tracking page returns `observe policy_rule option-check-tracking`.

**Act.** An overflowing sink returns `act policy_rule option-close-valve`.

**Approval.** A payment returns `act policy_rule option-pay` with `requires_approval = true`.

## Response basis

`decision.basis()` returns portable evidence rows:

```python
[
    {"kind": "reason", "ref": "within_risk_limit", "note": "risk is inside the limit"},
    {"kind": "reference", "ref": "sensor-1", "note": "water detected"},
]
```

The app can put these in its own audit record.

## Records

### What a record is

A record is a named data shape. It says which fields exist, what type they have and what values are
allowed. LAIX uses records for requests, decisions, outcomes and the lifecycle around them.

| Word | Meaning |
|---|---|
| **Record** | One data object, such as a decision or an outcome. |
| **Schema** | A machine-readable description of a record. |
| **Vector** | A fixed input and its expected output, used as a test case. |

Two versions travel with a decision, and they mean different things:

- `schema_version` is the version of the record shape.
- `policy_version` is the version of the rule set that produced the decision.

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

| Record | Carries |
|---|---|
| `Decision` | verb, chosen option, reason, confidence, alternatives, approval, target and ids |
| `EvidenceRef` | id, kind, quote, source and confidence |
| `Intent` | capability and args |
| `ScoreBreakdown` | severity, due, confidence, interruption, learned and total |

### Outcome and execution records

| Record | Carries |
|---|---|
| `Outcome` | decision id, metric, before/after, direction, attribution and label |
| `ExecutionReceipt` | chosen option, status, actor, result, idempotency key and error |
| `Trace` | ordered events for one decision |

`ExecutionReceipt` statuses are `pending`, `approved`, `executed`, `refused`, `cancelled`,
`failed`, `undone`, `unknown` and `duplicate`. A bridge may mark an action `unknown` and
reconcile it with provider evidence; a duplicate key returns a duplicate receipt.

Every core record carries `schema_version`.

### DecisionRecord lifecycle

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
| Package | `0.10.0` |
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

The schema is generated from the Python records, so it is the one decision schema. The test
vectors are hand-written and shared by both packages.
