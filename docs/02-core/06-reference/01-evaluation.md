# Evaluation

LAIX has three evaluation layers. They answer different questions.

| DecisionClient | Question | Location |
|---|---|---|
| **Core evaluation** | Did a policy or planner return the expected decision? | `core/evaluation/` |
| **Live decision benchmark** | Which planner is accurate and safe on the fixed live cases? | `core/engines/bench/` |
| **LAIX-Bench** | Does every decision class agree with its expected cases? | `appkit/bench/` |

The first two live in the core and have no CLI dependency. The third is an app-kit CLI and a
TypeScript mirror.

## Core evaluation

`Case`, `Row` and `Report` are the generic comparison primitives.

| Type | Fields |
|---|---|
| `Case` | `id`, `request`, `expected` |
| `Row` | `case_id`, `expected`, `actual`, `mismatches`; `passed` |
| `Report` | `rows`, `fields`; `total`, `passed`, `failed`, `agreement_rate`, `to_dict()` |

`Case.expected` is a tuple of mappings. `compare(cases, decide, *, fields=...)` runs the callable for
each case and compares the selected fields that the expected mapping contains. The default fields are
`verb`, `reason_code`, `deliver`, `record` and `requires_approval`.

```python
from laix import Case, compare, decide

cases = (
    Case(
        id="valve",
        request=request,
        expected=({"verb": "act", "reason_code": "policy_rule", "action_id": "valve"},),
    ),
)

report = compare(
    cases,
    lambda request: decide(request),
    fields=("verb", "reason_code", "action_id", "requires_approval"),
)
print(report.passed, report.total, report.agreement_rate)
```

Mismatches are strings such as `decision count 1 != 2` or `item 0: verb got != expected`.
`Report.agreement_rate` is `1.0` when there are no cases.

`load_cases(document, *, request_key="request", expected_key="expected")` reads a `cases` list from a
JSON document. `compare_decisions` is the package-level alias for `compare`.

### Attention evaluation

The attention fixture has its own helpers in `core/evaluation/signal_attention.py`:

| Helper | Purpose |
|---|---|
| `context_from(payload)` | Build a `SignalContext` from JSON keys. |
| `signal_from(payload)` | Build a `Signal` from JSON keys. |
| `run_case(case)` | Run one attention case. |
| `compare(case)` | Compare one case and return its mismatches. |
| `run_vectors(document)` | Run every vector. |
| `load_vectors(path)` | Load a vector file. |
| `validate_document(document)` | Validate the fixture shape and values. |
| `benchmark(document)` | Score `policy`, `severity_only` and `always_notify`. |
| `precision_recall(detected, known)` | Compute detected, known, matched, precision and recall. |

The attention fields are `verb`, `reason_code`, `deliver`, `record`, `requires_approval`, `score`,
`cost_of_waiting`, `undo_hint` and `reversible`.

The attention module also has a `compare(case)` for one vector. It is separate from the generic
`compare(cases, decide)` above: the generic helper takes a list and a callable, the attention helper
takes one attention case.

`benchmark` compares three policies: `policy`, `severity_only` and `always_notify`. It reports
`raised`, `helped`, `harmful`, `neutral`, `missed_helpful`, `precision`, `hazard` and `recall`.

Two fixture shapes exist:

- `validate_document` expects a case with a `signals` list;
- `benchmark` expects a case with one `signal` and a `label` of `helpful`, `harmful` or `neutral`.

They are separate formats. Use the validator with the vector shape and the benchmark with the
outcome shape.

## Live decision benchmark

The live decision benchmark compares training-free planners on fixed cases.

| Type | Fields |
|---|---|
| `LiveCase` | `name`, `problem`, `expected_actions`, `tags` |
| `LiveBenchRow` | `case`, `tags`, `planner`, `action_id`, `verb`, `expected`, `correct`, `safe`, `irreversible`, `latency_ms`, `score`, `reason_code` |
| `PlannerMetrics` | `planner`, `decisions`, `checked`, `correct`, `accuracy`, `safety_violations`, `irreversible`, `mean_latency_ms`, `mean_score`, `reasons` |
| `LiveBenchReport` | `rows`, `metrics`, `cases`, `planners`; `summary()`, `to_dict()` |

`LiveBenchReport.to_dict()` uses the keys `cases`, `planners`, `rows` and `metrics`. `summary()`
renders the metrics table, sorted by accuracy.

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

`default_planners()` returns seven keys in this order:

| Key | Planner |
|---|---|
| `first` | `FirstOptionPlanner` |
| `benefit` | `HighestBenefitPlanner` |
| `utility` | `UtilityPlanner` |
| `commitment` | `CommitmentPlanner` |
| `execution` | `ExecutionRiskPlanner` |
| `attention` | `HumanAttentionPlanner` |
| `live` | `LiveCompositePlanner` |

`FirstOptionPlanner` chooses the first option. `HighestBenefitPlanner` chooses the option with the
highest `expected_benefit`. Both return `wait` with `no_options` when the problem has no options.
They are comparison baselines outside the LAIX planner family.

`run_live_bench(cases=None, planners=None)` uses the defaults. It runs every planner on every case,
measures latency with `time.perf_counter()`, checks the chosen action against the expected actions,
checks safety against the hard constraints and records whether the chosen option is irreversible.

Accuracy is `correct / checked`, or `0.0` when no case has an expected action. `mean_score` is the
mean of the non-empty planner scores, or `None`. `reasons` is the sorted set of reason codes the
planner produced.

The external runner adds the `glue` key; `default_planners()` returns the seven keys above.

### Corpus and evidence

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

### JSON keys

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

`glue`, `first` and `benefit` are comparison baselines outside the LAIX planner family.

## LAIX-Bench

LAIX-Bench is the app-kit CLI. It runs one suite per decision class and reports agreement.

```powershell
python -m laix.appkit.bench
python -m laix.appkit.bench --list
python -m laix.appkit.bench --suite safety
python -m laix.appkit.bench --planners
python -m laix.appkit.bench --live
python -m laix.appkit.bench --json
```

The suites are `attention`, `action`, `active-perception`, `safety`, `replanning`, `allocation`,
`negotiation`, `preference`, `verification` and `escalation`. The current run covers 25 cases and
agrees on all 25.

The TypeScript mirror uses `npm run bench`, `npm run bench -- --suite safety`, `npm run bench --
--planners` and `npm run live-bench`.

The CLI, the case format and the stream bench are documented in
[LAIX-Bench](../../03-appkit/05-operate/01-bench.md).

## Conformance and parity

| Check | What it compares |
|---|---|
| `npm run conformance` | the signal-attention decisions against `packages/contracts/signal-attention.v1.json` |
| `npm run live-bench` | Python and TypeScript actions on the live corpus |
| `pytest` | Python contracts, policies, planners and app-kit behaviour |
| `npm test` | the same surface in TypeScript |

The conformance run agrees on 24/24 attention decisions. The live-bench parity check agrees on
210/210 action ids.

## What each check proves

| Check | Proves |
|---|---|
| Unit tests | the contract holds and a known regression stays fixed |
| LAIX-Bench | each decision class returns the expected verb, reason and action on its fixed cases |
| Live decision benchmark | the planners differ on the cases that isolate one concern |
| Frozen corpus | the reported accuracy, safety and latency on the documented split |
| Continuity benchmark | the mechanism uses state across decisions |

The evidence page describes the scope of each result.

## Related

- [Outcome learning](../05-learning/01-outcome-learning.md)
- [Calibration and model learning](../05-learning/02-calibration-and-model-learning.md)
- [Decision continuity](../04-continuity/01-decision-continuity.md)
- [LAIX-Bench](../../03-appkit/05-operate/01-bench.md)
- [Benchmark design](../../06-research/02-evaluation/benchmark.md)
