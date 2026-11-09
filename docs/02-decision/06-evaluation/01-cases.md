# Evaluation: cases and parity

Case evaluation answers one question: did a policy or planner return the expected decision on a fixed
case? It is the smallest proof layer and the base for the benchmarks.

| Layer | Question | Location |
|---|---|---|
| **Cases** | Did the decision match the expected fields? | `decision/evaluation/cases/` |
| **Bench** | Which planner is accurate and safe on the fixed corpus? | `decision/evaluation/bench/` |
| **Simulation** | How do planners compare on the same trace? | `decision/evaluation/simulation/` |

## Decision evaluation

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

## Attention evaluation

The attention fixture has its own helpers in `decision/evaluation/cases/signal_attention.py`:

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

## Conformance and parity

| Check | What it compares |
|---|---|
| `npm run conformance` | the signal-attention decisions against `packages/contracts/signal-attention.v1.json` |
| `npm run live-bench` | Python and TypeScript actions on the live corpus |
| `pytest` | Python contracts, policies, planners and app-kit behaviour |
| `npm test` | the same surface in TypeScript |

The conformance run agrees on 24/24 signal-attention decisions. The live-bench parity check agrees on
210/210 action ids.

## Related

- [Benchmarks](02-bench.md)
- [Simulation](03-simulation.md)
- [Continuity benchmark](04-continuity-benchmark.md)
- [Benchmark design](../../06-research/02-evaluation/benchmark.md)
