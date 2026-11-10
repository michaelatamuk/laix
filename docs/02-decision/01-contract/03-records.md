# Records

LAIX uses three related ideas:

| Word | Meaning |
|---|---|
| **Record** | One immutable data shape, such as `Decision`, `Situation` or `Outcome`. |
| **Schema** | A machine-readable description of the record fields, types and allowed values. |
| **Vector** | A fixed input and its expected output, used as a conformance test. |

The Python records are frozen dataclasses. The TypeScript records are readonly interfaces with the
same fields in camelCase. Both produce the same JSON values.

## The schema record set

The schema is generated from ten records. The set is declared in
`decision/schema/records.py` as `RECORDS` and `RECORD_NAMES`:

| Record | Module | Carries |
|---|---|---|
| `Observation` | `domain/decisions/request/payload/observation.py` | source, kind, confidence, payload, cost and latency |
| `Belief` | `domain/decisions/request/payload/belief.py` | proposition, confidence, evidence, update time and expiry |
| `Goal` | `domain/decisions/request/payload/goal.py` | statement, priority, metric, target and deadline |
| `Constraint` | `domain/decisions/request/payload/constraint.py` | kind, value, hard flag and statement |
| `ActionOption` | `domain/decisions/request/payload/action_option.py` | id, verb, name, expected benefit, cost, risk, latency, interruption, reversibility and approval |
| `Situation` | `domain/decisions/request/payload/situation.py` | observations, beliefs, goals, constraints, phase, horizon and attributes |
| `Outcome` | `domain/outcomes/record.py` | decision id, metric, before/after, delta, label, attribution and evidence |
| `ExecutionReceipt` | `domain/decisions/trail/execution_receipt.py` | action name, status, actor, result, idempotency key and error |
| `Trace` | `domain/decisions/trail/trace.py` | ordered events for one decision |
| `Decision` | `domain/decisions/response/decision.py` | verb, reason, confidence, action, approval, target and all audit fields |

`build_schema()` derives the JSON Schema from these dataclasses. The committed artefact is
`decision/schema/laix-v1.schema.json`. A test regenerates the schema and fails when the committed file is
stale.

`Trace.with_event(stage, detail=None, at=None)` returns a new trace with one appended event.

### Request record fields

**`Observation`**

| Field | Meaning |
|---|---|
| `id`, `at` | identity and observation time |
| `source`, `kind` | where it came from and what it measures |
| `confidence` | `0..1` |
| `payload` | host detail |
| `cost`, `latency_ms` | what the observation costs |

**`Belief`**

| Field | Meaning |
|---|---|
| `id`, `proposition` | identity and the held proposition |
| `confidence` | `0..1` |
| `evidence` | supporting reference ids |
| `updated_at`, `expires_at` | freshness and expiry |
| `source` | where the belief came from |

`Belief` adds `band` (`high`, `medium`, `low`), `expired(now)` and `decayed(now, half_life_minutes)`.

**`Goal`**

| Field | Meaning |
|---|---|
| `id`, `statement` | identity and the goal |
| `priority` | `0..1`, default `0.5` |
| `metric`, `target`, `deadline` | how the goal is measured and when |

**`Constraint`**

| Field | Meaning |
|---|---|
| `id` | identity |
| `kind` | `latency`, `cost`, `risk`, `interruption`, `approval`, `safety`, `budget` or `policy` |
| `value` | the limit or flag |
| `hard` | `True` means the limit may not be violated |
| `statement` | host explanation |

**`ActionOption`**

| Field | Meaning |
|---|---|
| `id`, `verb`, `name` | identity, verb and label |
| `params` | planner-specific facts |
| `expected_benefit` | `0..1`, default `0.5` |
| `cost`, `risk`, `latency_ms` | the ordinary costs |
| `interrupt_cost` | human interruption cost, `0..1` |
| `destructive` | implies `requires_approval` |
| `reversible` | whether the action can be undone |
| `requires_approval` | whether a person must approve |
| `addresses` | ids the option is meant to address |
| `rationale` | host explanation |

`ActionOption.utility` is the fixed tie-break value
`expected_benefit - 0.25 × risk - 0.15 × interrupt_cost`. It is not the `UtilityModel` score.

**`Situation`**

| Field | Meaning |
|---|---|
| `id`, `at`, `subject` | identity and moment |
| `observations`, `beliefs`, `goals`, `constraints` | the situation payload |
| `phase` | `observe`, `understand`, `decide`, `act`, `verify` or `adapt` |
| `horizon` | `seconds`, `minutes`, `hours`, `days` or `weeks` |
| `attributes` | host detail |

`Situation.confidence()` is the minimum belief confidence, else `attributes["confidence"]`, else
`0.0`. `Situation.uncertainty()` is `attributes["uncertainty"]`, else `1 - confidence`.

### Response payload fields

**`EvidenceRef`** carries `id`, `kind` (default `reference`), `quote`, `source` and `confidence`.

**`Intent`** carries `capability` and `args`. The host executes it.

**`ScoreBreakdown`** carries `severity`, `due`, `confidence`, `interruption`, `learned` and `total`.
It belongs to signal attention.

## Runtime shapes

Not every public shape is a schema record. These are runtime shapes that travel with a request or a
decision:

| Shape | Module | Role |
|---|---|---|
| `DecisionRequest` | `domain/decisions/request/decision_request.py` | the public request |
| `Signal` | `sensing/signals/input/signal.py` | one item that may need attention |
| `SignalContext` | `sensing/signals/input/signal_context.py` | time, quiet hours, thresholds, budget and feedback |
| `SignalFeedback` | `sensing/signals/input/signal_feedback.py` | the last response to a signal |
| `EvidenceRef` | `domain/decisions/response/payload/evidence_ref.py` | a reference that supports a decision |
| `Intent` | `domain/decisions/response/payload/intent.py` | capability and arguments the host can execute |
| `ScoreBreakdown` | `domain/decisions/response/payload/score_breakdown.py` | the parts of a signal-attention score |
| `Commitment` | `domain/commitments/commitment.py` | one promise with an owner, due time, trust source and dependencies |
| `CommitmentRef` | `domain/commitments/commitment_ref.py` | an owner-qualified reference to a commitment |
| `CommitmentLedger` | `domain/commitments/ledger.py` | the open promises for one task |
| `CommitmentGraph` | `domain/commitments/graph.py` | local and external commitments with blockers, cycles and impact |
| `CommitmentGraphReport` | `domain/commitments/graph.py` | missing refs, cycles and stale refs from `validate()` |
| `Detection`, `PerceptionEvent`, `PerceptionFrame` | `domain/perception/` | host-driven perception records |

These shapes have `to_dict()` where persistence matters. They sit outside the generated decision
schema, and the host owns their durable representation.

## `schema_version` and `policy_version`

A decision carries two versions that mean different things:

| Field | Version of | Bumps when |
|---|---|---|
| `schema_version` | the record shape | a field is added, removed or renamed |
| `policy_version` | the policy or planner that produced the decision | a rule, weight or threshold changes behaviour |

A record with `schema_version` is safe to read with the same major shape. A policy version change
means the decision behaviour changed even when the record shape did not.

The payload records `Situation`, `ActionOption`, `Constraint`, `Observation`, `Belief`, `Goal`,
`Outcome`, `ExecutionReceipt`, `Trace` and `Decision` carry `schema_version`. `DecisionRequest`,
`Signal`, `SignalContext`, `SignalFeedback` and `Commitment` do not.

## JSON

Python uses `to_dict()` and snake_case. TypeScript uses camelCase properties for the same concepts.
The JSON Schema uses the Python field names.

```python
decision = Decision(verb="act", confidence=0.9, reason_code="safe_action", rationale="inside risk")
payload = decision.to_dict()
restored = Decision.from_dict(payload)
```

The record round-trips through `to_dict()` and `from_dict()` without losing the nested evidence,
intent or score breakdown.

## Schema generation and validation

The schema is generated and validated with the helpers in
[Schema](../07-support/01-schema.md).

The schema enums come from the code:

| Constant | Field | Allowed values |
|---|---|---|
| `VERBS` | `verb` | `wait`, `observe`, `guide`, `ask`, `act`, `verify`, `escalate` |
| `PHASES` | `phase` | `observe`, `understand`, `decide`, `act`, `verify`, `adapt` |
| `HORIZONS` | `horizon` | `seconds`, `minutes`, `hours`, `days`, `weeks` |
| `EXECUTION_RECEIPT_STATUSES` | receipt `status` | `pending`, `approved`, `executed`, `refused`, `cancelled`, `failed`, `undone`, `unknown`, `duplicate` |
| `DECISION_STATUSES` | `Decision.status` | `final`, `provisional`, `superseded` |
| `TARGET_MODES` | `Decision.target` | `one`, `some`, `all`, `peer`, `gather` |
| `OUTCOME_LABELS` | `Outcome.label` | `helped`, `neutral`, `hurt`, `unknown` |
| `OUTCOME_DIRECTIONS` | `Outcome.direction` | `higher-better`, `lower-better` |
| `CONSTRAINT_KINDS` | `Constraint.kind` | `latency`, `cost`, `risk`, `interruption`, `approval`, `safety`, `budget`, `policy` |

## Version axes

| Thing | Version | Source |
|---|---|---|
| Package | `0.17.3` | `packages/python/laix/pyproject.toml`, `packages/typescript/laix/package.json` |
| Record schema | `0.8.0` | `decision/support/version.py`, `contracts.ts` |
| Rule sets | `0.8.0` | policy versions and vectors |
| Signal-attention vectors | `0.8.0` | `signal-attention.v1.json` and conformance fixtures |

The package, the schema and the rule sets move independently.

## Change rules

1. Change a record shape → bump the schema version and regenerate the schema.
2. Change a rule or threshold → bump the rule-set version.
3. Change a vector or weight → bump the vector version.
4. Add a decision class → add a policy with a name and version. The `Decision` shape stays the same.

A record change is a schema change. An additive field is preferred; removing or renaming a field
requires a new schema version and a migration note.

## Files

| File | Contents |
|---|---|
| `packages/python/laix/src/laix/decision/schema/laix-v1.schema.json` | generated schema for the ten records |
| `packages/contracts/decision-record.v1.schema.json` | the `DecisionRecord` shape from the app kit |
| `packages/contracts/decision.v1.schema.json` | the standalone `Decision` shape |
| `packages/contracts/reason-codes.v1.json` | the stable reason-code registry |
| `packages/contracts/signal-attention.v1.json` | signal-attention test cases |
| `packages/contracts/signal-attention-bench.v1.json` | signal-attention outcome cases |

`DecisionRecord`, `Approval`, `Undo` and `AuditEvent` belong to the app kit. See
[Execution and recovery](../../03-appkit/03-execute/01-execution-and-recovery.md).

## Related

- [Decision contract](01-decision-contract.md) — the request and response in prose.
- [Support helpers](../07-support/02-support.md) — ids, time, values and version.
- [Perception](../02-domain/04-perception.md) — detection, detector and frame.
- [Versioning](../../06-project/03-release/01-versioning.md) — the release and version policy.
