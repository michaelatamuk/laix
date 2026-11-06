# External validation data

Optional external validation materials. Nothing here is required for the synthetic benchmark; the
benchmark corpora live in `benchmarks/`.

Each folder is one validation method:

| Folder | What you do there |
|---|---|
| [`incident-replay/`](incident-replay/README.md) | replay historical incidents and compare LAIX with the human decision |
| [`vignette-study/`](vignette-study/README.md) | run the 20-vignette study and analyse participant choices |

Each method keeps generated output under `output/`, which is gitignored:

| Output | Produced by |
|---|---|
| `incident-replay/output/anonymised.jsonl` | `ingest_incidents.py` |
| `incident-replay/output/report.json` | `analyze_validation.py` |
| `vignette-study/v1/output/results.jsonl` | the offline app, saved by the facilitator |
| `vignette-study/v1/output/report.json` | `analyze_user_study.py` |

Do not commit raw incidents or participant results. See the README inside each method.
