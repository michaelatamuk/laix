# Repository structure

```text
laix/
├── packages/
│   ├── contracts/         JSON Schema and shared test vectors
│   ├── python/laix/       Python package and tests
│   └── typescript/laix/   TypeScript package and tests
├── docs/
│   ├── README.md          index
│   ├── design/            architecture, structure, decisions, contracts
│   ├── guides/            integration and capability guides
│   └── evaluation.md
├── examples/              runnable Python and TypeScript examples
└── .github/               CI and release workflows
```

`packages/contracts/` is the shared source of truth for data shapes and test vectors.

## Python package

```text
packages/python/laix/src/laix/
├── __init__.py              public API
├── contracts.py             ten core records
├── decisions.py             request and decision shapes
├── layer.py                 public Layer
├── platform.py              platform contract
├── policies/                action policy, eight packs, bandit, registry
├── attention/               attention policy and vectors
├── runtime/                 execution, state, stores, resources, perception
├── records/                 decision record and proposal
├── outcome.py               outcome ledger, store and UCB learner
├── delivery.py              delivery port
├── evaluation.py            parity harness
├── bench.py                 LAIX-Bench
├── schema.py                schema generator
└── schemas/                 generated schema
```

Import from `laix`; the subfolders are internal.

## TypeScript package

```text
packages/typescript/laix/src/
├── contracts.ts       core records
├── layer.ts           public Layer and action policy
├── attention.ts       attention policy
├── policies/          eight packs, bandit, registry
├── runtime/           execution, state, stores, resources, perception
├── platform.ts        platform contract
├── outcome.ts         outcome ledger and UCB learner
├── proposal.ts        proposal lifecycle
├── delivery.ts        delivery port
├── evaluation.ts      parity harness
├── bench.ts           LAIX-Bench
├── record.ts          decision record
├── index.ts           public exports
└── types.d.ts         public declarations
```

The TypeScript package mirrors the Python capabilities with camelCase names.

## Shared contracts

| File | Contents |
|---|---|
| `packages/contracts/decision.v1.schema.json` | decision and record shapes |
| `packages/contracts/decision-record.v1.schema.json` | decision record shape |
| `packages/contracts/attention.v1.json` | attention test cases |
| `packages/contracts/attention-bench.v1.json` | attention outcome cases |

The Python package keeps a copy of the attention vectors for installation. A test fails if the copy
and the canonical file differ.

## Rules

- One file per clear responsibility, until it gets too large.
- Group folders by role: `policies`, `runtime`, `records`, `attention`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words, not app, domain or vendor names.
