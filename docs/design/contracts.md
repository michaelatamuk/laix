# Contracts

## What a contract is

A contract is a named data shape. It says which fields exist, what type they have and what values are
allowed. LAIX uses contracts for requests, decisions, outcomes and the records around them.

| Word | Meaning |
|---|---|
| **Record** | One data object, such as a decision or an outcome. |
| **Schema** | A machine-readable description of a record. |
| **Vector** | A fixed input and its expected output, used as a test case. |
| **Policy version** | The label of the rule set that produced a decision. |

## One version

Everything in this release uses the same version: **0.6.0**.

| Thing | Version |
|---|---|
| Package | `0.6.0` |
| Record schema | `0.6.0` |
| Policy | `0.6.0` |
| Attention vectors | `0.6.0` |

There is one current shape and one current rule set. Old versions are not kept in the repository.
Tags keep history. If a change would break a caller, bump the package and update the callers in the
same pass.

## Files

| File | Contents |
|---|---|
| `packages/python/laix/src/laix/schemas/laix-v1.schema.json` | generated record schema |
| `packages/contracts/decision.v1.schema.json` | decision shapes |
| `packages/contracts/decision-record.v1.schema.json` | decision record shape |
| `packages/contracts/attention.v1.json` | attention test cases |
| `packages/contracts/attention-bench.v1.json` | attention outcome cases |

The schema is generated from the Python records. The test vectors are hand-written and shared by both
packages.

## The ten records

| Record | Carries |
|---|---|
| `Observation` | source, kind, confidence, payload, cost, latency |
| `Belief` | proposition, confidence, evidence, update time, expiry |
| `Goal` | statement, priority, metric, target, deadline |
| `Constraint` | kind, value, hard flag, statement |
| `Action` | verb, name, benefit, cost, risk, reversibility, approval |
| `Situation` | observations, beliefs, goals, constraints, phase, horizon |
| `Decision` | verb, action, rationale, alternatives, approval, audit ids |
| `Outcome` | metric, before/after, direction, attribution, label |
| `Receipt` | action, status, actor, result, error |
| `Trace` | ordered events for one decision |

Every record carries `schema_version = "0.6.0"`.

## JSON

Python records have `to_dict()` and use snake_case. The JSON Schema uses the same names. TypeScript
uses camelCase properties for the same concepts.

## Generate the schema

From `packages/python/laix`:

```powershell
py -c "from laix.schema import write_schema; write_schema()"
```

Check that the committed file is current:

```powershell
py -m pytest tests/test_laix.py -k schema
```

## Change rules

1. Change a record shape → bump the version and regenerate the schema.
2. Change a rule or threshold → bump the version.
3. Change an attention case or weight → bump the version.
4. Add a decision class → add a policy with a name and version. The decision shape stays the same.

The seven verbs are part of the contract: `wait`, `observe`, `guide`, `ask`, `act`, `verify`,
`escalate`.

## Where the rules live

- Action policy: `packages/python/laix/src/laix/policies/action.py`
- Attention policy: `packages/python/laix/src/laix/attention/policy.py`
- Policy pack inputs: [policy packs](../guides/policy-packs.md)
- Decision fields: [reading a decision](decisions.md)
