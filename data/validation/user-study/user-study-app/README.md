# User-study app

A self-contained, offline browser app for the 20-vignette study. It needs no external survey
platform and records no personal data.

## Run it

From the repository root:

```bash
python scripts/novelty/validation/serve_user_study.py
```

The browser opens at the printed local URL; the app itself is served under `/user-study-app/`.

## Facilitator flow

1. Give the participant the consent text in `docs/05-project/novelty/user-study-consent.md`.
2. Start the server and open the app.
3. The participant reads each scenario, sees one blinded recommendation, chooses an action and
   rates timeliness, trust and workload.
4. At the end, click **Download results**. Save the `.jsonl` file outside the repository.
5. Repeat for each participant with a fresh browser profile or by clearing local storage.

Each session is 20 vignettes × 2 recommendations = 40 trials, about 20–30 minutes.

## Output

The downloaded file is JSON Lines in the format expected by `scripts/novelty/validation/analyze_user_study.py`:

```json
{"participant_id":"p-...","vignette_id":"v01","condition":"laix","recommendation":"ask","choice":"ask","timeliness":5,"trust":4,"workload":2}
```

`condition` is hidden in the UI. The app randomises condition order, the A/B labels and the vignette
order.

## Privacy

- The participant id is random; there is no name or email field.
- Results stay in the browser until downloaded.
- Do not commit participant result files.
- Keep consent records separate from results.
