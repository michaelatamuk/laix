# LAIX-Bench

LAIX-Bench runs the same test cases in Python and TypeScript.

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
python -m laix.appkit.bench --json
```

TypeScript:

```powershell
npm.cmd run bench
npm.cmd run bench -- --suite safety --json
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

The runner compares `verb`, `reason_code`, `action_id` and `requires_approval`. Other fields are
ignored.

## Report

`run_bench()` returns:

- `total`, `passed`, `failed`, `agreement`;
- `by_suite()`;
- `to_dict()` for JSON.

## Add a case

1. Add it to `packages/python/laix/src/laix/appkit/bench/runner.py`.
2. Add the same case to `packages/typescript/laix/src/bench.ts`.
3. Run both benches.
4. Keep the case as a regression.

App traces can become cases by exporting the request and the expected decision. LAIX keeps its own
fixtures.

## Stream bench

`run_stream_bench(session, requests)` replays requests through a `StreamSession` and reports the
decisions, elapsed time, throughput and stream counters. See [streaming](streaming.md).
