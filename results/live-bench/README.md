# Live bench results

- Corpus: `benchmarks/live/v1/`
- Harness: `scripts/novelty/bench/run_live_bench.py`
- Current run: `harness-v2/`

`harness-v2/` separates raw output from reports:

| Path | Contents |
|---|---|
| `baseline.json` | frozen baseline used by `summarize_results.py` |
| `raw.jsonl` | one row per case and planner |
| `reports/summary.json` | current metrics |
| `reports/significance.json` | McNemar, bootstrap intervals and effect sizes |
| `reports/ablations.json` | ablation variants |
| `reports/typescript-parity.json` | Python/TypeScript action parity |
| `reports/external-comparison.json` | operational comparison with external adapters |
