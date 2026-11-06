# Vignette study

Fallback validation path: 20 short operational vignettes, each shown with a blinded recommendation.

`v1/` is the study instrument. Add `v2/` rather than editing v1 when the instrument changes.

## Instrument

| Path | Status | Contents |
|---|---|---|
| `v1/vignettes.json` | committed | the 20 vignettes, their options and both recommendations |
| `v1/app/` | committed | the offline browser app that presents the blinded study |
| `v1/output/results.jsonl` | generated | exported participant results |
| `v1/output/report.json` | generated | acceptance, trust, workload and agreement analysis |

`output/` is gitignored.

The protocol, consent text and recruitment template are in
[docs/05-project/novelty/user-study.md](../../docs/05-project/novelty/user-study.md).

## Run the study

From the repository root:

```bash
python scripts/novelty/validation/serve_user_study.py
```

The app blinds `laix_choice` and `baseline_choice`, randomises the vignette order and the A/B labels,
and downloads JSON Lines. Save the download as
`data/vignette-study/v1/output/results.jsonl`; concatenate participant files if you collect several.

## Analyse the results

```bash
python scripts/novelty/validation/analyze_user_study.py \
  --input data/vignette-study/v1/output/results.jsonl \
  --output data/vignette-study/v1/output/report.json
```

## Regenerate the vignettes

```bash
python scripts/novelty/validation/generate_vignettes.py
```
