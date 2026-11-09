# Contracts

The public contract is versioned here. Some files are canonical inputs; the decision schema and
reason-code registry are generated from the code and committed as stable artefacts.

| File | Contents |
|---|---|
| `decision-record.v1.schema.json` | the shape of an approval and audit record |
| `decision.v1.schema.json` | the standalone public `Decision` shape |
| `reason-codes.v1.json` | the stable reason-code registry |
| `a2a-agent-card.v1.json` | the A2A 1.0 agent card template |
| `action.openapi.v1.json` | the OpenAPI 3.1 host action profile |
| `signal-attention.v1.json` | 23 behavioural cases for the signal-attention policy |
| `signal-attention-bench.v1.json` | 12 labelled cases for precision, hazard and recall |

The decision shape is generated from the Python dataclasses in `laix.decision.decisions` and committed
as `packages/python/laix/src/laix/decision/schema/laix-v1.schema.json`. It ships inside the installed
package as the single decision schema.

A runtime is valid when it passes the cases for the policy it implements. Scores are part of the
signal-attention cases; a weight change creates a new major version.

The Python and TypeScript packages both read `signal-attention.v1.json`. The Python package keeps a copy
inside the package for installation; this folder is the canonical copy.

`decision.v1.schema.json` and `reason-codes.v1.json` are generated from the Python code. Regenerate
them from the repository root:

```powershell
python scripts/contracts/export_contracts.py
```

`a2a-agent-card.v1.json` and `action.openapi.v1.json` are host templates. Replace the placeholder URL
and security scheme before publishing; the checks only validate their structure.

