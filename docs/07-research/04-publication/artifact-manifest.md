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
- `scripts/novelty/bench/run_live_bench.py`
- `scripts/novelty/analysis/analyze_results.py`
- `scripts/novelty/bench/run_ablations.py`
- `scripts/novelty/bench/summarize_results.py`
- `scripts/novelty/shared/glue_baseline.py`
- `scripts/novelty/compare/run_external_comparison.py`
- `scripts/novelty/reproduce.sh`
- `scripts/novelty/shared/live_bench_common.py`
- `packages/typescript/laix/scripts/live-bench.mjs`
- `benchmarks/compare/README.md`
- `benchmarks/compare/adapters/` (protocol, result, LangGraph and Temporal adapters)
- `benchmarks/compare/capabilities.v1.json`
- `benchmarks/compare/requirements-external.txt`

## Results

- `results/live-decision-benchmark/metrics/baseline.json`
- `results/live-decision-benchmark/raw/decisions.jsonl`
- `results/live-decision-benchmark/metrics/summary.json`
- `results/live-decision-benchmark/metrics/significance.json`
- `results/live-decision-benchmark/ablations/results.json`
- `results/live-decision-benchmark/parity/typescript.json`
- `results/live-decision-benchmark/comparison/external-systems.json`

## Research docs

- `docs/07-research/README.md`
- `docs/07-research/01-positioning/prior-art.md`
- `docs/07-research/01-positioning/comparators.md`
- `docs/07-research/01-positioning/formal-model.md`
- `docs/07-research/02-evaluation/benchmark.md`
- `docs/07-research/02-evaluation/evidence-map.md`
- `docs/07-research/03-validation/plan.md`
- `docs/07-research/03-validation/incident-replay.md`
- `docs/07-research/03-validation/vignette-study.md`
- `docs/07-research/03-validation/consent.md`
- `docs/07-research/03-validation/recruitment.md`
- `docs/07-research/04-publication/publication-plan.md`
- `docs/07-research/04-publication/paper-draft.md`
- `docs/07-research/04-publication/references.md`
- `docs/07-research/04-publication/review-log.md`
- `docs/07-research/05-governance.md`
- `docs/07-research/checklist.md`

## Validation harness

- `data/README.md`
- `data/incident-replay/README.md`
- `data/incident-replay/template.jsonl`
- `data/vignette-study/README.md`
- `data/vignette-study/v1/vignettes.json`
- `data/vignette-study/v1/app/`
- `scripts/novelty/incident-replay/preflight_incidents.py`
- `scripts/novelty/incident-replay/ingest_incidents.py`
- `scripts/novelty/incident-replay/analyze_incident_replay.py`
- `scripts/novelty/vignette-study/generate_vignettes.py`
- `scripts/novelty/vignette-study/analyze_vignette_study.py`
- `scripts/novelty/vignette-study/serve_vignette_study.py`

## Reproduction

```bash
bash scripts/novelty/reproduce.sh
```

## Release fields

- Version: pending (current package version is `0.17.2`).
- Tag: pending.
- DOI: pending Zenodo deposit.
- License: Apache-2.0.
- Citation: `CITATION.cff`.
