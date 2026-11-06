# Artifact manifest

Use this list when preparing a Zenodo or GitHub release. The DOI and tag are intentionally pending.

## Benchmark

- `benchmarks/live/v1/schema.json`
- `benchmarks/live/v1/dev.json` (72)
- `benchmarks/live/v1/test.json` (30, frozen)
- `benchmarks/live/v1/adversarial.json` (18)
- `benchmarks/live/README.md`

## Analysis

- `scripts/novelty/bench/generate_live_cases.py`
- `scripts/novelty/bench/validate_live_cases.py`
- `scripts/novelty/bench/run_live_bench_v2.py`
- `scripts/novelty/analysis/analyze_results.py`
- `scripts/novelty/bench/run_ablations.py`
- `scripts/novelty/bench/summarize_results.py`
- `scripts/novelty/glue_baseline.py`
- `scripts/novelty/compare/run_external_comparison.py`
- `scripts/novelty/reproduce.sh`
- `scripts/novelty/live_bench_common.py`
- `packages/typescript/laix/scripts/live-bench.mjs`
- `benchmarks/compare/README.md`
- `benchmarks/compare/adapters/` (protocol, result, LangGraph and Temporal adapters)
- `benchmarks/compare/capabilities.v1.json`
- `benchmarks/compare/requirements-external.txt`

## Results

- `results/live-bench/harness-v2/baseline.json`
- `results/live-bench/harness-v2/raw.jsonl`
- `results/live-bench/harness-v2/reports/summary.json`
- `results/live-bench/harness-v2/reports/significance.json`
- `results/live-bench/harness-v2/reports/ablations.json`
- `results/live-bench/harness-v2/reports/typescript-parity.json`
- `results/live-bench/harness-v2/reports/external-comparison.json`

## Evidence

- `docs/05-project/novelty/README.md`
- `docs/05-project/novelty/prior-art.md`
- `docs/05-project/novelty/comparators.md`
- `docs/05-project/novelty/formal-model.md`
- `docs/05-project/novelty/evaluation.md`
- `docs/05-project/novelty/evidence.md`
- `docs/05-project/novelty/eu-liability.md`
- `docs/05-project/novelty/paper-draft.md`
- `docs/05-project/novelty/validation.md`
- `docs/05-project/novelty/checklist.md`

## Validation harness

- `docs/05-project/novelty/collection-kit.md`
- `data/README.md`
- `data/incident-replay/README.md`
- `data/incident-replay/template.jsonl`
- `data/vignette-study/README.md`
- `data/vignette-study/v1/vignettes.json`
- `data/vignette-study/v1/app/`
- `scripts/novelty/validation/check_validation_data.py`
- `scripts/novelty/validation/ingest_incidents.py`
- `scripts/novelty/validation/analyze_validation.py`
- `scripts/novelty/validation/generate_vignettes.py`
- `scripts/novelty/validation/analyze_user_study.py`
- `scripts/novelty/validation/serve_user_study.py`
- `docs/05-project/novelty/user-study.md`
- `docs/05-project/novelty/user-study-consent.md`
- `docs/05-project/novelty/user-study-recruitment.md`

## Reproduction

```bash
bash scripts/novelty/reproduce.sh
```

## Release fields

- Version: pending (current package version is `0.9.0`).
- Tag: pending.
- DOI: pending Zenodo deposit.
- License: Apache-2.0.
- Citation: `CITATION.cff`.
