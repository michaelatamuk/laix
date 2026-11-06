#!/usr/bin/env bash
set -euo pipefail

python scripts/validate_live_cases.py
python scripts/run_live_bench_v2.py --split test --seed 42
python scripts/analyze_results.py
python scripts/run_ablations.py --split test --seed 42
python scripts/summarize_results.py

echo "All live-bench checks passed"
