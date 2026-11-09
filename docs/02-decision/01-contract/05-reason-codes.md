# Reason codes

A **reason code** is the stable branch key on a decision. It says why the verb was chosen. App
logic branches on `reason_code`, never on `rationale`.

The machine-readable registry is
[`packages/contracts/reason-codes.v1.json`](../../../packages/contracts/reason-codes.v1.json).

## The registry

| Field | Meaning |
|---|---|
| `version` | Registry version. Bump it when a code is added, removed or renamed. |
| `schema_version` | The record-shape version this registry belongs to. |
| `extensible` | Authored rules may define their own code. |
| `groups` | Codes by producer. |
| `codes` | A flat sorted list for membership checks. |

The current groups:

| Group | Count | Examples |
|---|---:|---|
| `signal_attention` | 15 | `worth_surfacing`, `quiet_hours`, `kill_switch`, `overdue_escalation` |
| `planner` | 14 | `expected_utility`, `commitment_aware`, `live_decision`, `mdp_plan`, `pomdp_plan` |
| `policy` | 32 | `policy_rule`, `safe_action`, `no_safe_option`, `verify_outcome`, `replan`, `allocate` |
| `appkit` | 1 | `execution_step` |
| `bench` | 1 | `fixed_action` |

The signal-attention group is read from the `ReasonCode` enum, so it cannot drift from the gate
implementation. The planner and policy groups are listed in
`decision/contract/reason_codes.py`; a source-level test checks that every literal code in the Python
and TypeScript source is registered.

## Python

```python
from laix import reason_code_registry

registry = reason_code_registry()
assert "safe_action" in registry["codes"]
```

The registry is also available in `laix.decision.contract.reason_codes`.

## Rules

- Branch on `reason_code`; do not parse `rationale`.
- Treat an unknown code as policy-specific. Do not silently map it to a known code.
- A rename or removal is a behaviour change. Add a changelog entry and a migration note.
- A new authored-rule code can stay local, but publish it if an app or integration depends on it.
- The registry and the standalone decision schema are generated together:

```powershell
python scripts/contracts/export_contracts.py
```

The test suite fails if either committed file is stale.

## Related

- [Decision contract](01-decision-contract.md) - the request, response and reason-code contract.
- [Planner contract](02-planner-contract.md) - planner results.
- [Records](03-records.md) - the record schema and change rules.
- [Troubleshooting](../../06-project/02-quality/02-troubleshooting.md) - reason-code symptoms.
- [Versioning](../../06-project/03-release/01-versioning.md) - when a code change is a release change.
