# Repository structure

This page maps files. Concepts are defined in [architecture](../04-concepts/architecture.md),
[the Decision response](../02-core/01-decision-contract.md) and [records](../02-core/01-decision-contract.md).

```text
laix/
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
│   └── 05-project/        structure, testing, API map, versioning, roadmap
├── examples/
│   ├── python/            numbered lifecycle stages
│   └── typescript/        the same numbered stages
├── scripts/
│   └── check_docs_links.py relative link check for docs and READMEs
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
│   │   ├── engine.py        DecisionEngine, DecisionProblem, Plan, EnginePolicy, to_decision
│   │   ├── utility.py       UtilityEngine, UtilityModel and hard limits
│   │   ├── mdp.py           MdpModel, value iteration and MDPEngine
│   │   ├── pomdp.py         PomdpModel, belief update and POMDPEngine
│   │   ├── simulator.py     Simulator, scenarios and engine comparison
│   │   ├── calibration.py   CalibrationReport and confidence adjustment
│   │   ├── commitment_planner.py commitment-aware planning
│   │   ├── execution_planner.py execution-aware planning
│   │   ├── attention_planner.py attention-aware planning
│   │   ├── decision_calibration.py decision-level calibration
│   │   ├── live_bench.py    training-free live decision benchmark
│   │   ├── live_engine.py   integrated live planner
│   │   ├── model_learning.py ModelLearner and rollback
│   │   ├── policies/        policy.py, registry.py, simulation.py, implementations/ (packs, rules, target, planning, group)
│   │   ├── attention/       input, output, gates/, attention.v1.json, decide, score
│   │   └── resources/       budget, sensing option, plan, scheduler
│   ├── outcome_learning/    record, ledger, store, bandit, causal, rewards, attention/
│   ├── planning/            commitment ledger, stores and planning state
│   ├── evaluation/          case, row, report, compare, attention replay, attention-bench.v1.json
│   ├── sensing/             detection, detector, event, frame
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
│   ├── engine.ts      DecisionEngine, EnginePolicy and to_decision
│   ├── causal.ts      causal ledger
│   ├── planning.ts    commitment ledger
│   ├── planning-store.ts commitment stores
│   ├── utility.ts     utility engine
│   ├── mdp.ts         MDP model, value iteration and engine
│   ├── pomdp.ts       POMDP model, belief update and engine
│   ├── calibration.ts calibration report and smoothing
│   ├── commitment-planner.ts commitment-aware planner
│   ├── execution-planner.ts execution-aware planner
│   ├── attention-planner.ts attention-aware planner
│   ├── decision-calibration.ts decision-level calibration
│   ├── live-bench.ts training-free live benchmark
│   ├── live-engine.ts integrated live planner
│   ├── model-learning.ts count-based learner and MDP export
│   ├── outcome.ts     outcome ledger and UCB learner
│   ├── evaluation.ts  parity harness
│   ├── perception.ts  detector and frame contracts
│   ├── resources.ts   budget and resource admission
│   ├── attention.ts   attention policy
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
- Group folders by role: `decisions`, `policies`, `attention`, `runtime`, `audit`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words and leave app, domain and vendor names out.
