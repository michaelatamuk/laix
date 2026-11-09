# Repository structure

This page maps files. Concepts are defined in [architecture](../../04-concepts/01-architecture/01-system-architecture.md),
[the Decision response](../../02-core/01-contract/01-decision-contract.md) and [records](../../02-core/01-contract/03-records.md).

```text
laix/
├── README.md            product front page
├── CONTRIBUTING.md      setup, design rules and checks
├── SECURITY.md          vulnerability reporting
├── SUPPORT.md           where to ask
├── CODE_OF_CONDUCT.md   participation rules
├── CHANGELOG.md         release history
├── CITATION.cff         citation metadata
├── LICENSE              Apache-2.0
├── benchmarks/
│   ├── README.md          data vs harness index
│   ├── live/
│   │   └── v1/            schema, dev/test/adversarial corpus (frozen)
│   ├── continuity/
│   │   └── v1/            12-episode/60-decision continuity corpus
│   └── compare/           external adapters, capability matrix, requirements
├── data/
│   ├── README.md          validation methods index
│   ├── incident-replay/   incident replay input and output
│   └── vignette-study/
│       └── v1/            20-vignette instrument and app
├── results/
│   ├── live-decision-benchmark/
│   │   ├── raw/             per-case planner output
│   │   ├── metrics/         baseline, summary and significance
│   │   ├── ablations/       ablation study
│   │   ├── parity/          TypeScript parity
│   │   └── comparison/      external systems
│   ├── continuity-benchmark/
│   │   └── README.md        stateless vs stateful result
│   └── external/            external comparison output
├── packages/
│   ├── contracts/         JSON Schema and shared test vectors
│   ├── python/laix/       Python package and tests
│   └── typescript/laix/   TypeScript package and tests
├── docs/
│   ├── README.md          audience-first index
│   ├── 01-start/          overview; orientation/, first-steps/
│   ├── 02-core/           overview; contract/, domain/, decision/, sensing/, learning/, evaluation/, support/
│   ├── 03-appkit/         overview; build/, run/, execute/, connect/, operate/
│   ├── 04-concepts/       overview; architecture/, positioning/, trust/, reference/
│   ├── 05-project/        overview; repository/, quality/, release/, direction/
│   ├── 06-research/
│   │   ├── 01-positioning/  prior art, comparators, formal model
│   │   ├── 02-evaluation/   evaluation and evidence map
│   │   ├── 03-validation/   plan, incident replay and vignette study
│   │   ├── 04-publication/  paper, artifact, references and review
│   │   └── 05-governance.md  EU liability
│   └── assets/           logo, banner, architecture and demo placeholder
├── examples/
│   ├── data/              decision JSON for the CLI
│   ├── mcp/               MCP client config
│   ├── python/            core/ and appkit/, then decision shape
│   └── typescript/        the same core and app-kit split
├── scripts/
│   ├── ci/                repository checks (relative links and versions)
│   ├── novelty/
│   │   ├── bench/         corpus, live bench, ablations and baseline
│   │   ├── analysis/      significance tests and category breakdown
│   │   ├── compare/       external comparison runner
│   │   ├── incident-replay/  incident preflight, ingest and analysis
│   │   ├── vignette-study/   vignette generation, analysis and server
│   │   ├── shared/        shared benchmark and glue modules
│   │   └── reproduce.sh   full evidence pipeline
│   ├── contracts/         decision schema and reason-code exporter
│   └── docs/             brand asset renderer
└── .github/               CI and release workflows
```

`packages/contracts/` is the shared source of truth for the decision record shape, the standalone
decision schema, the reason-code registry and the test vectors. The core record schema is generated
from the Python dataclasses and ships inside the package.

`scripts/ci/check_docs_links.py` checks every relative link in the docs, examples and README files;
the `docs` CI job runs it.

## Python package

```text
packages/python/laix/src/laix/
├── __init__.py              public API
├── core/
│   ├── __init__.py          core surface
│   ├── dispatch.py          decide and select
│   ├── contract/             planner.py, planner_input.py, planner_result.py, planner_policy.py
│   ├── domain/
│   │   ├── decisions/        request, response, trail and normalise
│   │   ├── commitments/      commitment ledger, stores and planning state
│   │   ├── outcomes/         outcome record, ledger, store and signal-attention feedback
│   │   └── perception/       detection, detector, event and frame
│   ├── engines/
│   │   ├── decision/
│   │   │   ├── single/
│   │   │   │   ├── planners/
│   │   │   │   │   ├── utility/     utility planner, model and weights
│   │   │   │   │   ├── mdp/         MDP model, transitions, value iteration and planner
│   │   │   │   │   ├── pomdp/       POMDP model, observations, belief state and planner
│   │   │   │   │   ├── commitment/  commitment-aware planner, effects and weights
│   │   │   │   │   ├── execution/   execution-aware planner, effects and weights
│   │   │   │   │   ├── human_attention/   human-attention planner, budget and effects
│   │   │   │   │   ├── decision_value/    CA-VOD planner, weights and score
│   │   │   │   │   └── composite/         LiveCompositePlanner and composite score
│   │   │   │   └── policies/       decision_policy.py, registry, simulation and implementations/ (packs, rules, target, planning, group)
│   │   │   ├── sequence/           sequence contract, CABB, rollout and replan
│   │   │   ├── fleet/              attention scheduling and the exact Whittle index
│   │   │   ├── history/            continuity repair
│   │   │   └── explain/            attribution and counterfactual search
│   │   ├── sensing/
│   │   │   ├── signals/            input, output, gates/, signal-attention.v1.json, decide, score
│   │   │   └── resources/          budget, sensing option, plan, scheduler
│   │   ├── learning/
│   │   │   ├── calibration/        confidence and decision calibration
│   │   │   ├── model/              learned transition and model learning
│   │   │   ├── bandit/             arm, UCB learner and reward mapping
│   │   │   └── causal/             causal attribution
│   │   └── evaluation/
│   │       ├── cases/              case, row, report, compare, signal attention replay and signal-attention-bench.v1.json
│   │       ├── bench/              live benchmark, cases, rows, metrics and baselines
│   │       └── simulation/         simulator, scenario, step, result, report and planner score
│   ├── schema/              build, check, records and laix-v1.schema.json
│   └── support/             time, ids, values, serialize, errors, verbs, version
└── appkit/
    ├── __init__.py          optional app surface
    ├── decision_client.py   public DecisionClient
    ├── cli.py               laix explain and lint
    ├── mcp_server.py        optional laix-mcp stdio server
    ├── runtime/             decision loop, execution, saga, state, stores
    ├── audit/               decision record, proposal, approval, undo, audit event
    ├── delivery/            port, receipt, null
    ├── platform/            platform, in-memory, skill call, approvals, event, capability
    ├── live_context/        loop and callable detector
    ├── streaming/           session, window, sources, checkpoint, timeline, bench
    └── bench/               case, suite, row, report, runner, planner bench
```

Import from `laix` in app code, or `laix.core` / `laix.appkit` when the boundary matters. The package
ships `py.typed`, so type checkers use the inline annotations.

## TypeScript package

```text
packages/typescript/laix/src/
├── index.ts           public exports
├── core/
│   ├── index.ts       core surface
│   ├── contracts.ts   core records
│   ├── contract/planner.ts Planner, PlannerInput, PlannerResult, PlannerPolicy and toDecision
│   ├── domain/
│   │   ├── commitments/   commitment ledger and stores
│   │   ├── outcomes/      outcome ledger and stores
│   │   └── perception/perception.ts detector and frame contracts
│   ├── engines/
│   │   ├── decision/
│   │   │   ├── single/
│   │   │   │   ├── planners/
│   │   │   │   │   ├── utility/   utility planner and model
│   │   │   │   │   ├── mdp/       MDP model, value iteration and planner
│   │   │   │   │   ├── pomdp/     POMDP model, belief update and planner
│   │   │   │   │   ├── commitment/ commitment-aware planner
│   │   │   │   │   ├── execution/ execution-aware planner
│   │   │   │   │   ├── human-attention/ human-attention planner and budget
│   │   │   │   │   ├── decision-value/ CA-VOD planner, weights and score
│   │   │   │   │   └── composite/ LiveCompositePlanner
│   │   │   │   └── policies/      eight packs, bandit, rules, target, planning, group, shadow, decision-policy-registry
│   │   │   ├── sequence/          contract, CABB, rollout and replan
│   │   │   ├── fleet/             attention scheduling and the exact Whittle index
│   │   │   ├── history/           continuity repair
│   │   │   └── explain/           attribution and counterfactual search
│   │   ├── sensing/
│   │   │   ├── signals/signal-attention.ts signal-attention policy
│   │   │   └── resources.ts   budget and resource admission
│   │   ├── learning/
│   │   │   ├── calibration/   confidence and decision calibration
│   │   │   ├── model/         learned transition and model learning
│   │   │   ├── bandit/        UCB learner and reward mapping
│   │   │   └── causal/        causal ledger
│   │   └── evaluation/
│   │       ├── cases/evaluation.ts parity harness
│   │       └── bench/             live benchmark and baselines
└── appkit/
    ├── index.ts       optional app surface
    ├── decision-client.ts public DecisionClient and action policy
    ├── live-context.ts host-driven detector loop
    ├── streaming.ts   stream session and checkpoints
    ├── decision-timeline.ts decision timeline semantics
    ├── checkpoint.ts  in-memory and file checkpoint stores
    ├── simulator.ts   planner simulator and comparison
    ├── planner-bench.ts planner bench baseline
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
entry point, `laix`. `tsconfig.build.json` emits ESM JavaScript to `dist/`, while `types.d.ts` keeps
the curated public declaration surface. `prepare` rebuilds `dist/` before a local install or package
tarball.

## Shared spec

| File | Contents |
|---|---|
| `packages/contracts/decision-record.v1.schema.json` | decision record shape |
| `packages/contracts/decision.v1.schema.json` | standalone public decision shape |
| `packages/contracts/reason-codes.v1.json` | stable reason-code registry |
| `packages/contracts/a2a-agent-card.v1.json` | A2A 1.0 agent card template |
| `packages/contracts/action.openapi.v1.json` | OpenAPI 3.1 host action profile |
| `packages/contracts/signal-attention.v1.json` | signal-attention test cases |
| `packages/contracts/signal-attention-bench.v1.json` | signal-attention outcome cases |

The Python package keeps a copy of the signal-attention vectors for installation. A test fails if the copy
and the canonical file differ. The decision schema and reason-code registry are generated with
`python scripts/contracts/export_contracts.py`; a test fails if either committed file is stale.

## Rules

- One class per file; functions may share a small module with their owner.
- Layer `core` by role: `contract` (interfaces), `domain` (records and state), `engines` (processing) and `support`/`schema` (infrastructure).
- Group engine folders by decision shape: `decision/single`, `decision/sequence`, `decision/fleet`, `decision/history`, `decision/explain`; keep `sensing`, `learning` and `evaluation` as separate processing families.
- Mirror source folders in tests: `contract/`, `domain/`, `engines/`, `support/`, `schema/`.
- Keep the public API in `__init__.py` and `index.ts`.
- Use generic words and leave app, domain and vendor names out.
