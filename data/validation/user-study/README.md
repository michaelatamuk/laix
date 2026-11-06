# User study

Fallback validation path: 20 short operational vignettes, each shown with a blinded recommendation.

## Files

| File | Purpose |
|---|---|
| `vignettes-v1.json` | the 20 vignettes, their options and both recommendations |
| `user-study-app/` | the offline browser app that runs the study |
| `user-study-results.jsonl` | the exported results (not committed) |
| `user-study-report.json` | the analysis output (not committed) |

The protocol, consent text and recruitment template are in
[docs/05-project/novelty/user-study.md](../../../docs/05-project/novelty/user-study.md).

## Run the study

From the repository root:

```bash
python scripts/novelty/validation/serve_user_study.py
```

The app blinds `laix_choice` and `baseline_choice`, randomises the vignette order and the A/B labels,
and downloads JSON Lines.

## Analyse the results

```bash
python scripts/novelty/validation/analyze_user_study.py \
  --input data/validation/user-study/user-study-results.jsonl \
  --output data/validation/user-study/user-study-report.json
```

## Regenerate the vignettes

```bash
python scripts/novelty/validation/generate_vignettes.py
```
