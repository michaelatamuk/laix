# Repository structure

This page maps files. Concepts are defined in [architecture](architecture.md) and
[records](core/records.md).

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
│   ├── core/              records, decisions, attention, policies, learning, evaluation
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
│   ├── decisions/
│   │   ├── request/         situation, observation, belief, goal, constraint, option, request
│   │   ├── answer/          decision, evidence ref, intent, escalation, breakdown
│   │   ├── lifecycle/       receipt and trace
│   │   └── normalise.py     coerce and from_attention
│   ├── policies/
│   │   ├── builtin/action/  version, config, request and policy
│   │   ├── packs/           eight packs and the learned bandit
│   │   ├── policy.py        Policy protocol
│   │   ├── registry.py      PolicyRegistry
│   │   └── _support.py      shared pack helpers
│   ├── attention/
│   │   ├── model/           signal, context, feedback, decision, outcome
│   │   ├── ports/           clock, sink, recorder, defaults
│   │   ├── vectors/         attention.v1.json, bench.v1.json, schema.json
│   │   ├── decide.py        decide_one and decide_attention
│   │   ├── gates.py         gate order and feedback suppression
│   │   ├── score.py         score, cost of waiting, undo hint
│   │   ├── timing.py        quiet hours and windows
│   │   ├── replay.py        replay, validate and benchmark
│   │   ├── labels.py        outcome labels
│   │   └── outcome_log.py   bounded outcome log
│   ├── outcome/             record, ledger, store, arm, bandit, rewards
│   ├── evaluation/          case, row, report, compare
│   ├── perception/          detection, detector, event, frame
│   ├── resources/           budget, sensing option, plan, scheduler
│   ├── schema/              build, check, records and laix-v1.schema.json
│   └── support/             time, ids, values, serialize, errors, verbs, version
└── appkit/
    ├── __init__.py          optional app surface
    ├── layer.py             public Layer
    ├── runtime/             decision runtime, execution, state, stores
    ├── audit/               decision record, proposal, approval, undo, audit event
    ├── delivery/            port, receipt, null
    ├── platform/            platform, in-memory, skill call, approvals, event, capability
    ├── live_context/        loop and callable detector
    └── bench/               case, suite, row, report, runner
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

## Shared spec

| File | Contents |
|---|---|
| `packages/contracts/decision-record.v1.schema.json` | decision record shape |
| `packages/contracts/attention.v1.json` | attention test cases |
| `packages/contracts/attention-bench.v1.json` | attention outcome cases |

The Python package keeps a copy of the attention vectors for installation. A test fails if the copy
and the canonical file differ.

## Rules

- One class per file; functions may share a small module with their owner.
- Group folders by role: `decisions`, `policies`, `attention`, `runtime`, `audit`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words and leave app, domain and vendor names out.
