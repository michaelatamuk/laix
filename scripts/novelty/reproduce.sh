#!/usr/bin/env bash
set -euo pipefail

python scripts/novelty/bench/validate_live_cases.py
python scripts/novelty/bench/run_live_bench.py --split test --seed 42
python scripts/novelty/analysis/analyze_results.py
python scripts/novelty/bench/run_ablations.py --split test --seed 42
python scripts/novelty/bench/summarize_results.py
python scripts/novelty/bench/run_algorithm_bench.py
python scripts/novelty/bench/run_cabb_bench.py

echo "All novelty checks passed"
