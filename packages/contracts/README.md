# Contracts

The contract is the source of truth. Code follows it.

| File | Contents |
|---|---|
| `decision-record.v1.schema.json` | the shape of an approval and audit record |
| `attention.v1.json` | 23 behavioural cases for the attention policy |
| `attention-bench.v1.json` | 12 labelled cases for precision, hazard and recall |

The decision shape is generated from the Python dataclasses in `laix.core.contracts` and committed
as `packages/python/laix/src/laix/core/laix-v1.schema.json`. It ships inside the installed
package as the single decision schema.

A runtime is valid when it passes the cases for the policy it implements. Scores are part of the
attention cases; a weight change creates a new major version.

The Python and TypeScript packages both read `attention.v1.json`. The Python package keeps a copy
inside the package for installation; this folder is the canonical copy.

