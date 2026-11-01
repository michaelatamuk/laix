# Contracts and versions

LAIX data is versioned in three independent layers:

| Layer | Current | Changed when |
|---|---|---|
| **Record schema** | `1.1` | a field, type or enum changes |
| **Action policy** | `2026.2` | a rule, threshold or score weight changes |
| **Attention behaviour** | `2.2.0` | a vector, weight or reason changes |

A policy change does not require a schema change. A schema change always requires a new schema
version and a migration path.

## Source of truth

| Artefact | Location |
|---|---|
| Record schema | `packages/python/laix/src/laix/schemas/laix-v1.schema.json` |
| Decision and record shapes | `packages/contracts/decision.v1.schema.json`, `packages/contracts/decision-record.v1.schema.json` |
| Attention behaviour | `packages/contracts/attention.v1.json` |
| Attention metrics | `packages/contracts/attention-bench.v1.json` |

The schema is generated from the Python dataclasses. The behavioural vectors are hand-written and
language-neutral. Both packages implement the same contract.

## The ten records

| # | Record | What it carries |
|---|---|---|
| 1 | `Observation` | one measurement: source, kind, confidence, payload, cost and latency |
| 2 | `Belief` | a proposition with confidence, evidence, update time and expiry |
| 3 | `Goal` | what the experience improves, with priority, metric, target and deadline |
| 4 | `Constraint` | a latency, cost, risk, interruption, approval, safety, budget or policy limit |
| 5 | `Action` | a candidate verb with benefit, cost, risk, reversibility and approval need |
| 6 | `Situation` | observations, beliefs, goals, constraints, phase and horizon |
| 7 | `Decision` | chosen verb, action, rationale, alternatives, approval and audit ids |
| 8 | `Outcome` | metric, before/after, direction, attribution and label |
| 9 | `Receipt` | pending, approved, executed, refused, failed, cancelled or undone execution |
| 10 | `Trace` | ordered evidence for one decision |

Every record carries `schema_version = "1.1"`.

## Serialisation

- Python records expose `to_dict()` and use snake_case field names on the wire.
- The canonical JSON Schema uses the same snake_case names.
- The TypeScript SDK exposes idiomatic camelCase properties for the same concepts.

What is shared is the meaning and the shape, not the spelling of every property in every language.

## Generate the schema

From `packages/python/laix`:

```powershell
py -c "from laix.schema import write_schema; write_schema()"
```

The staleness test regenerates it and fails if the committed file differs:

```powershell
py -m pytest tests/test_laix.py -k schema
```

## Versioning rules

1. **Additive record change** → new minor schema version. Old readers keep working.
2. **Removal or meaning change** → new major schema version. Keep the old version available.
3. **Policy threshold or score change** → bump the policy version, not the schema.
4. **Attention weight or reason change** → new major attention contract; vectors are the evidence.
5. **New decision class** → new policy name and version. No change to the decision shape.

The seven verbs are part of the schema:

```text
wait, observe, guide, ask, act, verify, escalate
```

Approval is the `requires_approval` flag. There is no `notify` verb.

## Where the rules live

- Action rule order and thresholds: `packages/python/laix/src/laix/policies/action.py`.
- Attention scoring and gates: `packages/python/laix/src/laix/attention/policy.py`.
- Reference pack inputs and outputs: [policy packs](../guides/policy-packs.md).
- How to read the returned fields: [decisions](decisions.md).
