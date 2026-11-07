# Live decision benchmark results

Corpus: `benchmarks/live/v1/`
Runner: `scripts/novelty/bench/run_live_bench.py`

| Folder | Contents |
|---|---|
| `raw/` | per-case planner output |
| `metrics/` | frozen baseline, current metrics and significance tests |
| `ablations/` | ablation study |
| `parity/` | TypeScript parity check |
| `comparison/` | operational comparison with external systems |

| File | Contents |
|---|---|
| `raw/decisions.jsonl` | one row per case and planner |
| `metrics/baseline.json` | frozen metrics used by `summarize_results.py` |
| `metrics/summary.json` | current metrics |
| `metrics/significance.json` | McNemar, bootstrap intervals and effect sizes |
| `ablations/results.json` | ablation variants |
| `parity/typescript.json` | Python/TypeScript action parity |
| `comparison/external-systems.json` | operational comparison with external adapters |

Regenerate the reports with `bash scripts/novelty/reproduce.sh`.

## Planner keys

The JSON files use the short code keys. The docs use the full class names. A key is a stable data
identifier; it does not have to match a class name.

| Key | Component | Type |
|---|---|---|
| `live` | `LiveDecisionEngine` | engine |
| `glue` | hand-built glue baseline | external baseline |
| `commitment` | `CommitmentPlanner` | planner |
| `execution` | `ExecutionRiskPlanner` | planner |
| `attention` | `HumanAttentionPlanner` | planner |
| `utility` | `UtilityPlanner` | planner |
| `first` | `FirstOptionPlanner` | naive baseline |
| `benefit` | `HighestBenefitPlanner` | naive baseline |

`glue`, `first` and `benefit` are comparison baselines, not LAIX planners.
