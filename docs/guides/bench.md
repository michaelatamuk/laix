# LAIX-Bench

LAIX-Bench v0 runs deterministic cases across every decision class. It has no app data, no network
and no randomness, so a failure is reproducible.

## Run

```powershell
python -m laix.bench
python -m laix.bench --list
python -m laix.bench --suite safety
python -m laix.bench --json
python -m laix.bench --fail-under 1.0
```

```text
suite                     cases  passed  agreement
---------------------------------------------------
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
---------------------------------------------------
overall                      25      25      1.000
```

The process exits `0` when agreement meets `--fail-under`, otherwise `1`.

## Suites

| Suite | Decision class |
|---|---|
| `attention` | which signal deserves attention now |
| `action` | which available action to take |
| `active-perception` | look before deciding when uncertainty is high |
| `safety` | act only inside the hard risk limit |
| `replanning` | choose a replacement plan |
| `allocation` | fund a portfolio under a budget |
| `negotiation` | accept, counter or escalate |
| `preference` | ask the question that reduces uncertainty most |
| `verification` | confirm that an action worked |
| `escalation` | hand over to a named target |

Each suite has one policy factory and an ordered list of cases.

## Case format

```python
BenchCase(
    id="safety_safe_option",
    request=DecisionRequest(...),
    expected={"verb": "act", "reason_code": "safe_action", "action_id": "valve"},
)
```

The runner compares the expected subset of `verb`, `reason_code`, `action_id` and
`requires_approval`. Extra fields on the decision are allowed.

## Report

`run_bench()` returns a `BenchReport`:

- `total`, `passed`, `failed`, `agreement`;
- `by_suite()` with cases, passed, failed and agreement per class;
- `to_dict()` for JSON.

A mismatch row names the suite, the case, the expected value and the actual value.

## Add a case

1. Add a `BenchCase` to the suite in `laix/bench.py`.
2. Run `python -m laix.bench`.
3. If it fails, decide whether the case or the policy is wrong.
4. Keep the case; it is now a regression.

## Boundary

The bench uses generic situations and attributes. App logs become bench cases by exporting the same
decision request and the expected decision; LAIX never imports the app. The fixtures stay in LAIX;
real traces can be added as a separate suite without changing the runner.
