# Benchmarks

Benchmarks answer a different question from a case test: which planner is accurate, safe and fast on a
fixed corpus, and does the ranking hold across decision classes?

| Benchmark | Question | Location |
|---|---|---|
| **Live decision benchmark** | Which training-free planner is accurate and safe on the fixed live cases? | `decision/engines/evaluation/bench/` |
| **LAIX-Bench** | Does every decision class agree with its expected cases? | `appkit/bench/` |
| **Parity** | Do Python and TypeScript agree on the same corpus? | `results/live-decision-benchmark/parity/` |

## Live decision benchmark

The live decision benchmark compares training-free planners on fixed cases.

| Type | Fields |
|---|---|
| `LiveCase` | `name`, `problem`, `expected_actions`, `tags` |
| `LiveBenchRow` | `case`, `tags`, `planner`, `action_id`, `verb`, `expected`, `correct`, `safe`, `irreversible`, `latency_ms`, `score`, `reason_code` |
| `PlannerMetrics` | `planner`, `decisions`, `checked`, `correct`, `accuracy`, `safety_violations`, `irreversible`, `mean_latency_ms`, `mean_score`, `reasons` |
| `LiveBenchReport` | `rows`, `metrics`, `cases`, `planners`; `summary()`, `to_dict()` |

`default_cases()` returns seven cases:

| Case | Tag | Expected | What it separates |
|---|---|---|---|
| `risk_limit` | safety | `safe` | hard risk limit 0.4; safe 0.6/0.1 vs risky 0.9/0.6 |
| `commitment` | commitment | `send-later` | commitment `c1` due; send-now violates, send-later fulfills |
| `irreversible` | execution | `archive` | delete-now is irreversible; archive is reversible |
| `unknown` | execution | `known` | unknown option has `unknown_risk=0.8` |
| `approval` | execution | `direct` | approval option requires approval |
| `attention` | attention | `act` | budget 0.2, spent 0.2; ask 0.9 vs act 0.6 |
| `plain` | utility | `bold` | safe 0.6/0.1 vs bold 0.9/0.6 |

`default_planners()` returns seven keys: `first`, `benefit`, `utility`, `commitment`, `execution`,
`attention` and `live`. The first two are comparison baselines outside the LAIX planner family.

`run_live_bench(cases=None, planners=None)` uses the defaults. It runs every planner on every case,
measures latency with `time.perf_counter()`, checks the chosen action against the expected actions,
checks safety against the hard constraints and records whether the chosen option is irreversible.

## Corpus and evidence

| Split | Cases |
|---|---:|
| dev | 72 |
| test | 30 |
| adversarial | 18 |
| **total** | **120** |

The corpus is in `benchmarks/live/v1/`; the frozen result is in
`results/live-decision-benchmark/`. The current test-split result:

| Measure | `LiveCompositePlanner` | Best comparator |
|---|---:|---:|
| Accuracy, 30 cases | 100% | 93.3% (glue baseline) |
| Conflict accuracy, 6 cases | 100% | 100% (glue baseline) |
| Promise keeping | 100% | 100% (glue baseline) |
| Irreversible actions | 0% | 0% (glue baseline) |
| Attention-budget violations | 0% | 0% (glue baseline) |

The +6.7 pp difference over glue is not significant on 30 cases (p = 0.48). The benchmark is a
fixed synthetic corpus. The design and the measured evidence are in
[the benchmark page](../../06-research/02-evaluation/benchmark.md).

## JSON keys

The result files use short keys. They are stable data identifiers; they are not class names.

| Key | Component |
|---|---|
| `live` | `LiveCompositePlanner` |
| `glue` | hand-built glue baseline |
| `commitment` | `CommitmentPlanner` |
| `execution` | `ExecutionRiskPlanner` |
| `attention` | `HumanAttentionPlanner` |
| `utility` | `UtilityPlanner` |
| `first` | `FirstOptionPlanner` |
| `benefit` | `HighestBenefitPlanner` |

## LAIX-Bench

LAIX-Bench is the app-kit regression suite that runs one suite per decision class. The CLI, the case
format, the suites and the stream bench are documented in
[LAIX-Bench](../../03-appkit/05-operate/01-bench.md).

## What the decision layer benchmarks prove

- The live benchmark separates planners on the cases that isolate one concern.
- The frozen corpus reports accuracy, safety and latency on the documented split.
- The continuity benchmark shows that state carries across decisions.

## Related

- [Cases and parity](01-cases.md)
- [Simulation](03-simulation.md)
- [Continuity benchmark](04-continuity-benchmark.md)
- [Benchmark design](../../06-research/02-evaluation/benchmark.md)
- [LAIX-Bench](../../03-appkit/05-operate/01-bench.md)
