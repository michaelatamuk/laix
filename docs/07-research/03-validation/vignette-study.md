# Vignette study protocol

Status: materials are ready; no participants have been recruited.

## Materials

`data/vignette-study/v1/vignettes.json` contains 20 vignettes. Each vignette has:

- `situation` — plain-English description;
- `options` — labelled actions;
- `laix_choice` — the current LAIX recommendation;
- `baseline_choice` — the current utility-only recommendation;
- `human_choice` and `notes` — empty until the study.

The offline app lives in `data/vignette-study/v1/app/`. Start it with:

```bash
python scripts/novelty/vignette-study/serve_vignette_study.py
```

It blinds the recommendations, randomises order and downloads the results JSONL.

## Design

- Within-subject: each participant sees both recommendations for each vignette.
- 30 participants, 20 vignettes, 2 conditions = 1,200 trials.
- Randomise condition order per participant and vignette.
- Blind the condition label: show "Recommendation A" and "Recommendation B".
- Collect consent and IRB/ethics approval before starting.

## Procedure

1. Show the situation and the options.
2. Show one recommendation with its rationale.
3. Ask the participant to choose an action and rate the recommendation on:
   - timeliness (1–5);
   - trust (1–5);
   - workload (1–5, reversed for analysis).
4. Repeat for the other condition.
5. Record whether the participant's choice matches the recommendation.

## Results format

One JSON object per trial in JSON Lines:

```json
{"participant_id": "p01", "vignette_id": "v01", "condition": "laix", "recommendation": "ask", "choice": "ask", "timeliness": 5, "trust": 4, "workload": 2}
```

`condition` is `laix` or `baseline`. `recommendation` is the action id shown in that condition.

## Analysis

- Agreement rate per condition, with a paired bootstrap 95% CI.
- Mean timeliness, trust and workload per condition.
- Paired difference per participant and vignette, with a bootstrap CI.
- Wilcoxon signed-rank test when SciPy is available; otherwise a two-sided sign test.
- Fleiss' kappa for participant agreement per vignette and condition.
- Report the number of participants, exclusions and missing trials.

Script:

```bash
python scripts/novelty/vignette-study/analyze_vignette_study.py --input data/vignette-study/v1/output/results.jsonl
```

## Sample-size justification

The study is powered for a medium paired effect. Record the assumed effect size, the resulting
power and any deviation from this plan in `plan.md`.

## Limitations to write up

- Vignettes are not real incidents.
- Participants may anchor on the recommendation.
- The order and the labels are counterbalanced, but the study is still artificial.
- Results complement deployment evidence.
