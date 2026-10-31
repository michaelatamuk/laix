# Repository structure

## Top level

```text
laix/
├── contracts/        canonical JSON Schema and behavioural vectors
├── docs/             design, decisions, contracts, evaluation, integration
├── examples/         small runnable requests and caller examples
├── python/laix/      the Python package and its tests
├── typescript/laix/  the TypeScript package and its tests
├── scripts/          repository test runner
└── .github/          CI and release workflows
```

`contracts/` is the source of truth for data. The packages implement it.

## Python package

```text
python/laix/src/laix/
├── __init__.py              public exports; `from laix import ...` stays stable
├── contracts.py             the core records
├── decisions.py             the decision/request shapes and conversions
├── layer.py                 the public Layer orchestrator
├── platform.py              the south platform interface and in-memory platform
├── policies/
│   ├── action.py            the built-in action policy
│   └── registry.py          the policy plugin interface
├── attention/               the attention policy
├── runtime/
│   ├── decision_runtime.py  the action runtime
│   ├── execution.py         approval, execute, cancel, undo
│   ├── state.py             experience state
│   ├── state_store.py       the storage-free state store contract
│   └── resources.py         resource policy
├── records/
│   ├── decision.py          the decision record
│   └── proposal.py          the proposal lifecycle
├── outcome.py               the metric outcome ledger
├── delivery.py              the delivery port and receipt
├── evaluation.py            the parity harness
├── schema.py                schema generation
└── schemas/                 the generated schema file
```

The top level is the public API. The subfolders are internal organisation; an app
imports from `laix`, not from the internal paths.

## TypeScript package

```text
typescript/laix/src/
├── attention.ts   attention policy and its types
├── layer.ts       the public Layer and action policy
├── record.ts      the decision record
├── index.ts       the public exports
└── types.d.ts     the public TypeScript declarations
```

## Size rules

- A module stays one file until it has two clear responsibilities or grows past roughly
  500–700 lines.
- A folder is added when a group has a real boundary, not to reduce a file count.
- Generated files and data files are allowed to be larger than code files.
- `typescript/attention.ts` is medium and cohesive. `contracts.py` holds ten related
  dataclasses. Neither needs a split yet.
- `schemas/laix-v1.schema.json` is generated. `contracts/attention.v1.json` is test data.

## Duplicated contracts

The attention vectors and bench exist twice:

- `contracts/` — canonical.
- `python/laix/src/laix/attention/contract/` — packaged copy for installation.

`tests/test_contract_copies.py` fails if the two copies differ.

## Naming rules

- Group by responsibility: `policies`, `runtime`, `records`, `attention`.
- Keep the public API in `laix/__init__.py`.
- Use words that describe the role, not the app.
- Do not add app names, domains or vendor words to the package.
