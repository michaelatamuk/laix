# Bench

LAIX-Bench runs the same test cases in Python and TypeScript. It is a deterministic regression suite,
not a claim about production accuracy.

| Word | Meaning |
|---|---|
| **Case** | One request and the decision it should produce. |
| **Suite** | A group of cases for one decision class. |
| **Agreement** | The share of cases that produced the expected decision. |

It uses fixed cases, local execution and deterministic ordering, so failures reproduce.

## Run

Python:

```powershell
python -m laix.appkit.bench
python -m laix.appkit.bench --list
python -m laix.appkit.bench --suite safety
python -m laix.appkit.bench --planners
python -m laix.appkit.bench --json
```

TypeScript:

```powershell
npm.cmd run bench
npm.cmd run bench -- --suite safety --json
npm.cmd run bench -- --planners
```

```text
suite                     cases  passed  agreement
attention                     3       3      1.000
action                        3       3      1.000
active-perception             2       2      1.000
safety                        2       2      1.000
replanning                    2       2      1.000
allocation                    2       2      1.000
negotiation                   3       3      1.000
preference                    2       2      1.000
verification                  3       3      1.000
escalation                    3       3      1.000
overall                      25      25      1.000
```

Both exit `0` when agreement meets `--fail-under`, otherwise `1`.

## Suites

| Suite | Question |
|---|---|
| `attention` | Which signal deserves attention now? |
| `action` | Which option should we choose? |
| `active-perception` | Should we look first? |
| `safety` | Is any option inside the risk limit? |
| `replanning` | Which replacement plan fits? |
| `allocation` | What fits the budget? |
| `negotiation` | Accept, counter or escalate? |
| `preference` | Which question should we ask? |
| `verification` | Did the chosen option work? |
| `escalation` | Should we hand over? |

## Case

```python
BenchCase(
    id="safety_safe_option",
    request=DecisionRequest(...),
    expected={"verb": "act", "reason_code": "safe_action", "action_id": "valve"},
)
```

`BenchCase` carries `id`, `request` and `expected`. `FIELDS` defines the compared fields:
`verb`, `reason_code`, `action_id` and `requires_approval`. Other fields are ignored.

## Report

`run_bench()` returns a `BenchReport`:

- `total`, `passed`, `failed`, `agreement`;
- `by_suite()`, a per-suite agreement map;
- `to_dict()` for JSON;
- `rows`, a tuple of `BenchRow`.

`BenchRow` carries `suite`, `case`, `expected`, `actual`, `mismatches` and `passed`.
`Suite` carries `name`, `description`, `policy` and `cases`.

`all_suites()` and `suite_names()` return the registered suites. `run_bench()` runs them.

## Add a case

1. Add it to `packages/python/laix/src/laix/appkit/bench/runner.py`.
2. Add the same case to `packages/typescript/laix/src/bench.ts`.
3. Run both benches.
4. Keep the case as a regression.

App traces can become cases by exporting the request and the expected decision. LAIX keeps its own
fixtures.

## Stream bench

`run_stream_bench(session, requests)` replays requests through a `StreamSession` and returns a
`StreamBenchResult` with `decisions`, `elapsed_ms`, `throughput_per_second` and `stats`. See
[Streaming](../02-run/02-streaming.md).

## Planner simulation

`python -m laix.appkit.bench --planners` compares `MDPPlanner` with a do-nothing baseline on a chain
and prints reward, steps and optimality gap. `--json` returns the same rows as JSON.
`run_planner_bench()` is the Python entry point. The `Simulator`, `Scenario`, `SimulationReport`,
`SimulationResult`, `SimulationStep`, `compare_planners` and `seeded_scenarios` mechanisms are on the
[planner contract](../../02-core/03-planning/01-planner-contract.md#simulator).

## Live decision benchmark

`python -m laix.appkit.bench --live` runs the seven-case live decision benchmark. The cases, planner
keys, corpus and measured results are on the
[evaluation page](../../02-core/06-reference/01-evaluation.md#live-decision-benchmark).

```powershell
python -m laix.appkit.bench --live
python -m laix.appkit.bench --live --json
```

TypeScript exports the same benchmark as `runBench`, `runStreamBench`, `runPlannerBench`,
`runLiveBench`, `suiteNames`, `allSuites`, `comparePlanners`, `seededScenarios`, `defaultCases` and
`liveBenchSummary`. The planner simulation types are `FixedActionPlanner`, `RandomStep`,
`PlannerScore` and `SimulatorOptions`.

## What it proves

- The decision classes return the expected verb, reason, action and approval flag on fixed cases.
- A change that breaks a class fails in CI.
- Python and TypeScript agree on the same fixtures.

## What it does not prove

- Production accuracy.
- That the corpus covers a customer's domain.
- That a benchmark win is adoption.

The external evidence and its limits are in the
[claim-evidence map](../../06-research/02-evaluation/evidence-map.md).

## Related

- [Metrics](02-metrics.md) - the counters and latency.
- [Streaming](../02-run/02-streaming.md) - the stream bench.
- [Evaluation](../../02-core/06-reference/01-evaluation.md) - cases, reports and parity.
- [Deployment](03-deployment.md) - the production checklist.
