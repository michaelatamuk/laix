#!/usr/bin/env bash
set -euo pipefail

python scripts/run_live_bench_v2.py --split test --seed 42
python scripts/run_ablations.py --split test --seed 42
python scripts/summarize_results.py

echo "All live-bench checks passed"
