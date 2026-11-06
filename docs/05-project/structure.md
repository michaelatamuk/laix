# Repository structure

This page maps files. Concepts are defined in [architecture](../04-concepts/architecture.md),
[the Decision response](../02-core/01-decision-contract.md) and [records](../02-core/01-decision-contract.md).

```text
laix/
├── benchmarks/
│   └── live/              case schema, dev/test/adversarial corpus
├── results/
│   └── live_bench_v2/     summaries, ablations and raw rows
├── packages/
│   ├── contracts/         JSON Schema and shared test vectors
│   ├── python/laix/       Python package and tests
│   └── typescript/laix/   TypeScript package and tests
├── docs/
│   ├── README.md          audience-first index
│   ├── 01-start/          quickstart, what-is, lifecycle, host integration
│   ├── 02-core/           contract, attention, policies, learning, evaluation, planners
│   ├── 03-appkit/         architecture, integration, streaming, execution, stores, bench
│   ├── 04-concepts/       architecture, boundaries, PPMA, decision models, privacy, FAQ, glossary
│   └── 05-project/        structure, testing, API map, versioning, roadmap, novelty/
├── examples/
│   ├── python/            numbered lifecycle stages
│   └── typescript/        the same numbered stages
├── scripts/
│   ├── check_docs_links.py relative link check
│   └── novelty/           live corpus, bench, ablations, validation and reproduction
└── .github/               CI and release workflows
```

`packages/contracts/` is the shared source of truth for the decision record shape and the test
vectors. The core record schema is generated from the Python dataclasses and ships inside the
package.

`scripts/check_docs_links.py` checks every relative link in the docs, examples and README files;
the `docs` CI job runs it.

## Python package

```text
packages/python/laix/src/laix/
├── __init__.py              public API
├── core/
│   ├── __init__.py          core surface
│   ├── decisions/
│   │   ├── request/         decision_request.py envelope; payload records
│   │   ├── response/        decision.py; payload: evidence ref, intent, score breakdown
│   │   ├── trail/           execution receipt and trace
│   │   └── normalise.py     coerce and from_attention
│   ├── engines/
│   │   ├── contract/       engine.py, decision_engine.py, decision_problem.py, plan.py
│   │   ├── planners/
│   │   │   ├── utility/     utility engine, model and weights
│   │   │   ├── mdp/         MDP model, transitions, value iteration and engine
│   │   │   ├── pomdp/       POMDP model, observations, belief state and engine
│   │   │   ├── commitment/  commitment-aware planner, effects and weights
│   │   │   ├── execution/   execution-aware planner, effects and weights
│   │   │   ├── attention/   attention-aware planner, budget and effects
│   │   │   └── live/        integrated live planner and score
│   │   ├── simulation/     simulator, scenario, step, result, report and engine score
│   │   ├── learning/       calibration, decision calibration and model learning
│   │   ├── bench/          live benchmark, cases, rows, metrics and baselines
│   │   ├── signals/        input, output, gates/, attention.v1.json, decide, score
│   │   ├── policies/       policy.py, registry.py, simulation.py, implementations/ (packs, rules, target, planning, group)
│   │   └── resources/      budget, sensing option, plan, scheduler
│   ├── outcome_learning/    record, ledger, store, bandit, rewards, causal/, attention/
│   ├── commitments/         commitment ledger, stores and planning state
│   ├── evaluation/          case, row, report, compare, attention replay, attention-bench.v1.json
│   ├── perception/          detection, detector, event, frame
│   ├── schema/              build, check, records and laix-v1.schema.json
│   └── support/             time, ids, values, serialize, errors, verbs, version
└── appkit/
    ├── __init__.py          optional app surface
    ├── layer.py             public Layer
    ├── runtime/             decision runtime, execution, saga, state, stores
    ├── audit/               decision record, proposal, approval, undo, audit event
    ├── delivery/            port, receipt, null
    ├── platform/            platform, in-memory, skill call, approvals, event, capability
    ├── live_context/        loop and callable detector
    ├── streaming/           session, window, sources, checkpoint, timeline, bench
    └── bench/               case, suite, row, report, runner, engine bench
```

Import from `laix` in app code, or `laix.core` / `laix.appkit` when the boundary matters.

## TypeScript package

```text
packages/typescript/laix/src/
├── index.ts           public exports
├── core/
│   ├── index.ts       core surface
│   ├── contracts.ts   core records
│   ├── contract/engine.ts DecisionEngine, EnginePolicy and to_decision
│   ├── commitments/   commitment ledger and stores
│   ├── causal.ts      causal ledger
│   ├── planners/
│   │   ├── utility/   utility engine and model
│   │   ├── mdp/       MDP model, value iteration and engine
│   │   ├── pomdp/     POMDP model, belief update and engine
│   │   ├── commitment/ commitment-aware planner
│   │   ├── execution/ execution-aware planner
│   │   ├── attention/ attention-aware planner and budget
│   │   └── live/      integrated live planner
│   ├── learning/      calibration, decision calibration and model learning
│   ├── bench/         live benchmark and baselines
│   ├── outcome.ts     outcome ledger and UCB learner
│   ├── evaluation.ts  parity harness
│   ├── perception/perception.ts detector and frame contracts
│   ├── resources.ts   budget and resource admission
│   ├── signals/attention.ts attention policy
│   └── policies/      eight packs, bandit, rules, target, planning, group, shadow, registry
└── appkit/
    ├── index.ts       optional app surface
    ├── layer.ts       public Layer and action policy
    ├── live-context.ts host-driven detector loop
    ├── streaming.ts   stream session and checkpoints
    ├── decision-timeline.ts decision timeline semantics
    ├── checkpoint.ts  in-memory and file checkpoint stores
    ├── simulator.ts   engine simulator and comparison
    ├── engine-bench.ts engine bench baseline
    ├── window.ts      tumbling windows
    ├── sources.ts     queue, sync, NDJSON and SSE sources
    ├── metrics.ts     Prometheus counters
    ├── bench-stream.ts stream bench
    ├── record.ts      decision record
    ├── platform.ts    platform contract
    ├── proposal.ts    proposal lifecycle
    ├── delivery.ts    delivery port
    ├── bench.ts       LAIX-Bench
    └── runtime/       execution, saga, state and stores
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
- Group folders by role: `contract`, `planners`, `simulation`, `learning`, `bench`, `commitments`, `perception`, `policies`, `signals`.
- Mirror source folders in tests: `contract/`, `planners/`, `simulation/`, `learning/`, `bench/`, `commitments/`, `perception/`, `policies/`, `signals/`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words and leave app, domain and vendor names out.
