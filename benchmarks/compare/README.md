# External comparison harness

The external comparison is deliberately separate from the synthetic decision-accuracy benchmark.

External systems are not decision planners. LangGraph and Temporal orchestrate state, approvals and
recovery; they do not choose the LAIX verb. A fair comparison therefore measures:

- capability coverage;
- integration effort;
- latency overhead;
- dependencies;
- approval/interrupt behaviour;
- audit and recovery support.

It does **not** claim that `live` beats LangGraph or Temporal at decision accuracy. That would compare
different tasks.

## Adapters

| Adapter | Runnable here | What it shows |
|---|---|---|
| `langgraph_adapter.py` | optional, needs `langgraph` | a state graph with a decision node and an approval interrupt |
| `temporal_adapter.py` | template, needs a Temporal server | durable execution, retries, signals and compensation |
| PagerDuty / Camunda | documented only | alerting and BPMN approval/compensation |

## Install the optional dependency

```bash
python -m pip install -r benchmarks/compare/requirements-external.txt
```

Then run:

```bash
python scripts/novelty/compare/run_external_comparison.py --split test
```

The script writes `results/live_bench_v2/external-comparison.json` and prints the capability and
operational table.

## Fairness rules

- Use the same case split and the same `DecisionProblem` inputs.
- Put the same `LiveDecisionEngine` inside each framework; the framework owns orchestration, not the
  decision.
- Report which parts are runnable and which are documented only.
- Report dependencies and glue code, not only latency.
- Never present a documented capability comparison as a measured performance result.

## Measured result

The LangGraph adapter ran on all 120 cases:

| Metric | Result |
|---|---:|
| Decisions | 120 |
| Approval interrupts | 0 |
| Mean latency | 6-7 ms |
| Adapter glue code | 110 lines |
| Dependencies | `langgraph` |

This is an orchestration comparison, not an accuracy comparison: the same LAIX engine is inside the
graph. Temporal, PagerDuty and Camunda remain documented-only because they need a server or account.

## Capability matrix

`capability-matrix.json` is the machine-readable version of the documented comparison in
`docs/05-project/novelty/comparators.md`.
