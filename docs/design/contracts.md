# Contracts and versions

Two questions have two different answers:

- **Which package do I install?** The package version: `0.6.0`.
- **Which shape and rules produced this record?** `schema_version` and `policy_version`.

## Version labels

| Label | Current | What it identifies | Where it appears |
|---|---|---|---|
| **Package** | `0.6.0` | the release you install | tag, pip, npm |
| **Record schema** | `1.1` | the JSON field shape | every record's `schema_version` |
| **Action policy** | `2026.2` | the built-in action rule set | `decision.policy_version` |
| **Attention vectors** | `2.2.0` | the behavioural test set | `packages/contracts/attention.v1.json` |

These are labels for different things, not three versions of LAIX. `1.1` is not older than `2026.2`;
they count different objects. The action policy label is date-coded: `2026.2` means the 2026 rule
set, revision 2.

- A package release happens for any change.
- The schema changes only when a field, type or enum changes.
- A policy version changes when its rules, thresholds or weights change.
- The attention vector version changes when its cases or expected decisions change.

The package is the only version an app pins.

## Compatibility

LAIX is pre-1.0. The repository ships **one current schema** and **one current rule set**. There is no
old-version support matrix to maintain. When a change would break an existing caller, bump the
package and update the callers in the same pass. Tags keep the history; the main branch carries only
the current shape.

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

1. **Field, type or enum change** → bump the package and the schema, then regenerate the schema.
2. **Rule, threshold or score change** → bump the package and that policy's version.
3. **Attention case, weight or reason change** → bump the package and the attention vector version.
4. **New decision class** → new policy name and version; the decision shape stays the same.
5. **Breaking shape change** → bump the package and update every caller in the same pass. The old
   shape is not carried forward.

The seven verbs are part of the schema:

```text
wait, observe, guide, ask, act, verify, escalate
```

Approval is the `requires_approval` flag. A decision to notify someone uses the `guide` verb; the app
chooses the delivery channel.

## Where the rules live

- Action rule order and thresholds: `packages/python/laix/src/laix/policies/action.py`.
- Attention scoring and gates: `packages/python/laix/src/laix/attention/policy.py`.
- Reference pack inputs and outputs: [policy packs](../guides/policy-packs.md).
- How to read the returned fields: [decisions](decisions.md).
