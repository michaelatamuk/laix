# Testing

CI runs the same checks locally.

## Python

```powershell
cd packages/python/laix
python -m pytest -q
ruff check .
python -m laix.appkit.bench
```

Live benchmark, ablations and baseline diff from the repository root:

```powershell
python scripts/novelty/bench/generate_live_cases.py
python scripts/novelty/bench/validate_live_cases.py
python scripts/novelty/bench/run_live_bench.py --split test --seed 42
python scripts/novelty/analysis/analyze_results.py
python scripts/novelty/bench/run_ablations.py --split test --seed 42
python scripts/novelty/bench/summarize_results.py
```

CI runs the same sequence through `bash scripts/novelty/reproduce.sh`.

External comparison is optional and needs an extra dependency:

```powershell
python -m pip install -r benchmarks/compare/requirements-external.txt
python scripts/novelty/compare/run_external_comparison.py --split all
```

With `uv` from the repository root:

```powershell
uv run --directory packages/python/laix --with pytest python -m pytest -q
uvx ruff check packages/python/laix
```

Python examples:

```powershell
$env:PYTHONPATH = "packages/python/laix/src"
Get-ChildItem examples/python -Recurse -Filter *.py | ForEach-Object { py $_.FullName }
```

`tests/test_examples.py` also runs every Python example.

## TypeScript

```powershell
cd packages/typescript/laix
npm ci
npm run typecheck
npm run typecheck:declarations
npm test
npm run bench
npm run conformance
npm run live-bench
```

TypeScript examples:

```powershell
Get-ChildItem examples/typescript -Recurse -Filter *.mts | ForEach-Object {
    node --experimental-strip-types $_.FullName
}
```

## Current results

| Check | Result |
|---|---|
| Python tests | passed |
| Invariant tests | 17/17 |
| TypeScript tests | 172 passed |
| Signal-attention conformance | 24/24 |
| LAIX-Bench | 25/25 |
| 7-case live demo | `LiveCompositePlanner` 7/7 |
| Live corpus | 120 cases: 72 dev / 30 test / 18 adversarial |
| Live decision benchmark | test split: `LiveCompositePlanner` 30/30; conflict 6/6 |
| Glue baseline | 28/30; `LiveCompositePlanner` +6.7 pp, p = 0.48 |
| External validation | pending |
| Ablations | full 100%, no commitment 70%, no execution 83.3%, no human attention 96.7% |
| Analysis | McNemar, paired bootstrap and effect sizes |
| TS live parity | 210/210 action IDs match Python on the test split |
| LangGraph adapter | 120 decisions, 0 interrupts, 6-7 ms mean, 110 glue lines |

## Docs

```powershell
python scripts/ci/check_docs_links.py
```

The check resolves relative links across `docs/`, root Markdown files and every `README.md`.

## What covers what

| Check | Covers |
|---|---|
| `pytest` | contracts, policies, planners, calibration, timeline, app kit, schema, examples |
| `tests/core/test_invariants.py` | determinism, hard gates, budget, approval, revision, receipts, trace, confidence, contract and parity infrastructure |
| `ruff check` | Python syntax, undefined names and unused imports |
| `tsc` | TypeScript source and public declaration syntax/types |
| `npm test` | TS contracts, conformance, parity, streaming, timeline, execution, planners |
| `npm run bench` | 10 suites and 25 deterministic cases |
| `npm run conformance` | 24 shared signal-attention decisions |
| `npm run live-bench` | TypeScript runs the 30-case test split and compares 210 action IDs with Python |
| `scripts/novelty/bench/run_live_bench.py` | 120-case corpus, metrics, bootstrap intervals, conflict check |
| `scripts/novelty/analysis/analyze_results.py` | McNemar, paired bootstrap, Cohen's h and category breakdown |
| `scripts/novelty/bench/run_ablations.py` | term removal, equal weights and no-feasibility-gates variants |
| `scripts/novelty/bench/summarize_results.py` | baseline diff for headline metrics |
| `scripts/novelty/bench/validate_live_cases.py` | JSON Schema validation and duplicate-id check |
| `scripts/novelty/incident-replay/` | incident preflight, ingest and analysis |
| `scripts/novelty/vignette-study/` | vignette generation, study analysis and server |
| `scripts/ci/check_docs_links.py` | relative links in docs, examples and README files |
| `benchmarks/live/v1/` | versioned corpus and schema |
| `benchmarks/compare/adapters/` | optional external adapters and capability matrix |
| examples | every runnable Python and TypeScript example |
| docs links | relative links in docs, examples and README files |

## CI

`.github/workflows/ci.yml` runs Python on 3.11 and 3.13, TypeScript on Node 22 and 24, and the docs
link check. `.github/workflows/release.yml` runs the same checks before building a tagged release.
