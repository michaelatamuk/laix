#!/usr/bin/env bash
set -euo pipefail

python scripts/novelty/validate_live_cases.py
python scripts/novelty/run_live_bench_v2.py --split test --seed 42
python scripts/novelty/analyze_results.py
python scripts/novelty/run_ablations.py --split test --seed 42
python scripts/novelty/summarize_results.py

echo "All live-bench checks passed"
