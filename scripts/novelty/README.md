# Novelty tooling

Scripts for the live benchmark, its analysis, external comparison and validation collection. Run
everything from the repository root.

| Folder | Contents |
|---|---|
| `bench/` | corpus generation, schema validation, the live bench, ablations and the baseline summary |
| `analysis/` | paired significance tests and per-category breakdown |
| `compare/` | the optional external comparison runner |
| `incident-replay/` | incident preflight, ingest and analysis |
| `vignette-study/` | vignette generation, study analysis and the local app server |
| `shared/` | modules used by more than one stage |

`bench/` reads `benchmarks/live/v1/`. `incident-replay/` reads `data/incident-replay/`.
`vignette-study/` reads `data/vignette-study/v1/`.

Run the full pipeline:

```bash
bash scripts/novelty/reproduce.sh
```
