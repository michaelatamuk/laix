# Artifact manifest

Use this list when preparing a Zenodo or GitHub release. The DOI and tag are intentionally pending.

## Benchmark

- `benchmarks/live/cases.v1.schema.json`
- `benchmarks/live/dev-cases-v1.json` (72)
- `benchmarks/live/test-cases-v1.json` (30, frozen)
- `benchmarks/live/adversarial-cases-v1.json` (18)
- `benchmarks/live/README.md`

## Analysis

- `scripts/novelty/generate_live_cases.py`
- `scripts/novelty/validate_live_cases.py`
- `scripts/novelty/run_live_bench_v2.py`
- `scripts/novelty/analyze_results.py`
- `scripts/novelty/run_ablations.py`
- `scripts/novelty/summarize_results.py`
- `scripts/novelty/glue_baseline.py`
- `scripts/novelty/reproduce.sh`
- `scripts/novelty/live_bench_common.py`
- `packages/typescript/laix/scripts/live-bench.mjs`

## Results

- `results/live_bench_v2/summary.json`
- `results/live_bench_v2/baseline.json`
- `results/live_bench_v2/analysis.json`
- `results/live_bench_v2/ablations.json`
- `results/live_bench_v2/raw.jsonl`
- `results/live_bench_v2/typescript-summary.json`

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
- `data/validation/README.md`
- `data/validation/incidents-template.jsonl`
- `data/validation/vignettes-v1.json`
- `scripts/novelty/check_validation_data.py`
- `scripts/novelty/ingest_incidents.py`
- `scripts/novelty/analyze_validation.py`
- `scripts/novelty/generate_vignettes.py`
- `scripts/novelty/analyze_user_study.py`
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
