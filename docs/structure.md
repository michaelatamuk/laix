# Repository structure

This page maps files. Concepts are defined in [architecture](architecture.md) and
[contracts](core/contracts.md).

```text
laix/
├── packages/
│   ├── contracts/         JSON Schema and shared test vectors
│   ├── python/laix/       Python package and tests
│   └── typescript/laix/   TypeScript package and tests
├── docs/
│   ├── README.md          index
│   ├── what-is-laix.md    plain-English introduction
│   ├── host-integration.md six questions a host team asks
│   ├── architecture.md    how LAIX fits together
│   ├── boundaries.md      core, app kit and host
│   ├── positioning.md     LAIX and decision models
│   ├── structure.md       this page
│   ├── core/              contracts, decisions, attention, policies, learning, evaluation
│   └── appkit/            integration, live context, platform, stores, bench
├── examples/              runnable Python and TypeScript examples
└── .github/               CI and release workflows
```

`packages/contracts/` is the shared source of truth for the decision record shape and the test
vectors. The core record schema is generated from the Python dataclasses and ships inside the
package.

## Python package

```text
packages/python/laix/src/laix/
├── __init__.py              public API
├── core/
│   ├── __init__.py          core surface
│   ├── contracts.py         nine shared records, enums and helpers
│   ├── decisions.py         Decision, DecisionRequest and normalisation
│   ├── outcome.py           outcome ledger, store and UCB learner
│   ├── evaluation.py        parity harness
│   ├── perception.py        detector, detection and frame contracts
│   ├── resources.py         budget and resource admission policy
│   ├── schema.py            schema generator
│   ├── laix-v1.schema.json  generated record schema
│   ├── attention/           attention policy and vectors
│   └── policies/            action policy, eight packs, bandit, registry
└── appkit/
    ├── __init__.py          optional app surface
    ├── layer.py             public Layer
    ├── live_context.py      host-driven detector loop
    ├── platform.py          platform contract
    ├── delivery.py          delivery port
    ├── bench.py             LAIX-Bench implementation
    ├── runtime/             execution, state and stores
    └── records/             decision record and proposal
```

Import from `laix` in app code, or `laix.core` / `laix.appkit` when the boundary matters.

## TypeScript package

```text
packages/typescript/laix/src/
├── index.ts           public exports
├── core/
│   ├── index.ts       core surface
│   ├── contracts.ts   core records
│   ├── outcome.ts     outcome ledger and UCB learner
│   ├── evaluation.ts  parity harness
│   ├── perception.ts  detector and frame contracts
│   ├── resources.ts   budget and resource admission
│   ├── attention.ts   attention policy
│   └── policies/      eight packs, bandit, registry
└── appkit/
    ├── index.ts       optional app surface
    ├── layer.ts       public Layer and action policy
    ├── live-context.ts host-driven detector loop
    ├── record.ts      decision record
    ├── platform.ts    platform contract
    ├── proposal.ts    proposal lifecycle
    ├── delivery.ts    delivery port
    ├── bench.ts       LAIX-Bench
    └── runtime/       execution, state and stores
```

The TypeScript package mirrors the same folders under `src/core` and `src/appkit`. It exports one
entry point, `laix`.

## Shared contracts

| File | Contents |
|---|---|
| `packages/contracts/decision-record.v1.schema.json` | decision record shape |
| `packages/contracts/attention.v1.json` | attention test cases |
| `packages/contracts/attention-bench.v1.json` | attention outcome cases |

The Python package keeps a copy of the attention vectors for installation. A test fails if the copy
and the canonical file differ.

## Rules

- One file per clear responsibility, until it gets too large.
- Group folders by role: `policies`, `runtime`, `records`, `attention`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words and leave app, domain and vendor names out.
