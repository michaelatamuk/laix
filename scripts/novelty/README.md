# Novelty tooling

Scripts for the live benchmark, its analysis, external comparison and validation collection. Run
everything from the repository root.

| Folder | Contents |
|---|---|
| `bench/` | corpus generation, schema validation, the live bench, ablations and the baseline summary |
| `analysis/` | paired significance tests and per-category breakdown |
| `validation/` | user-study generation and analysis, incident ingest and preflight, the local app server |
| `compare/` | the optional external comparison runner |

`bench/` reads `benchmarks/live/v1/`. `validation/` reads `data/incident-replay/` and
`data/vignette-study/v1/`. `live_bench_common.py` and `glue_baseline.py` are shared modules used by
both `bench/` and `validation/`.

Run the full pipeline:

```bash
bash scripts/novelty/reproduce.sh
```
