# Repository structure

## Top level

```text
laix/
├── packages/
│   ├── contracts/         canonical JSON Schema and behavioural vectors
│   ├── python/laix/       the Python package and its tests
│   └── typescript/laix/   the TypeScript package and its tests
├── docs/
│   ├── README.md          documentation index
│   ├── design/            architecture, structure, decisions, contracts
│   ├── guides/            integration and capability guides
│   └── evaluation.md      vectors, conformance and what to add next
├── examples/              runnable requests and caller examples
└── .github/               CI and release workflows
```

`packages/contracts/` is the source of truth for data. Both language packages implement it.

## Python package

```text
packages/python/laix/src/laix/
├── __init__.py              public API; `from laix import ...`
├── contracts.py             the ten core records and version constants
├── decisions.py             the decision/request shapes used by Layer
├── layer.py                 the public Layer orchestrator
├── platform.py              south platform contract and in-memory platform
├── policies/
│   ├── action.py            built-in action policy
│   ├── active_perception.py reference observe policy
│   ├── safety.py            risk-limited action policy
│   ├── replanning.py        feasible-plan selection policy
│   ├── allocation.py        budgeted allocation policy
│   ├── negotiation.py       accept, counter or escalate policy
│   ├── preference.py        preference-question selection policy
│   ├── verification.py      outcome confirmation policy
│   ├── escalation.py        hand-over policy
│   ├── bandit.py            learned bandit policy
│   └── registry.py          policy plugin protocol and registry
├── attention/               attention policy, scoring, feedback and contracts
├── runtime/
│   ├── decision_runtime.py  action runtime and trace
│   ├── execution.py         approval, execute, cancel, undo
│   ├── perception.py        live context: detectors, admission, frames
│   ├── state.py             experience state
│   ├── state_store.py       state store contract and in-memory store
│   └── resources.py         cheap/deep admission policy
├── records/
│   ├── decision.py          decision record lifecycle
│   └── proposal.py          proposal lifecycle
├── outcome.py               outcome ledger, store contract and UCB learner
├── delivery.py              delivery port and receipt
├── evaluation.py            parity harness
├── bench.py                 LAIX-Bench suites, report and CLI
├── schema.py                schema generation
└── schemas/                 committed generated schema
```

The top level of `laix` is the public API. Subfolders are internal organisation; an app imports
from `laix`, not from an internal path.

## TypeScript package

```text
packages/typescript/laix/src/
├── attention.ts       attention policy and its types
├── bench.ts           LAIX-Bench suites and report
├── contracts.ts       core records and helpers
├── delivery.ts        delivery port and receipt
├── evaluation.ts      parity harness
├── layer.ts           public Layer and action policy
├── outcome.ts         ledger, store contract and UCB learner
├── platform.ts        south platform contract and in-memory platform
├── proposal.ts        proposal lifecycle
├── record.ts          decision record lifecycle
├── policies/          eight packs, bandit policy and registry
├── runtime/           execution, state, stores, resources and perception
├── index.ts           public exports
└── types.d.ts         public TypeScript declarations
```

The package mirrors the Python capabilities with idiomatic TypeScript naming (`reasonCode`,
`actionId`, camelCase).

## Contracts

`packages/contracts/` holds canonical data:

| File | Contents |
|---|---|
| `decision.v1.schema.json` | decision and surrounding record shapes |
| `decision-record.v1.schema.json` | approval and audit record shape |
| `attention.v1.json` | behavioural cases for the attention policy |
| `attention-bench.v1.json` | labelled cases for precision, hazard and recall |

The Python package keeps an installed copy of the attention vectors under
`packages/python/laix/src/laix/attention/contract/`. `tests/test_contract_copies.py` fails if the
copies drift from `packages/contracts/`.

## Size rules

- A module stays one file until it has two clear responsibilities or grows past roughly 500–700
  lines.
- A folder is added for a real boundary, not to reduce a file count.
- Generated and data files may be larger than code files.
- `attention.ts` is medium and cohesive. `contracts.py` holds ten related records. Neither needs a
  split yet.
- `schemas/laix-v1.schema.json` is generated; `packages/contracts/attention.v1.json` is test data.

## Naming rules

- Group by responsibility: `policies`, `runtime`, `records`, `attention`.
- Keep the public API in `laix/__init__.py` and `src/index.ts`.
- Name the role, not the app, domain or vendor.
- Do not add app names, domain nouns or vendor words to either package.
