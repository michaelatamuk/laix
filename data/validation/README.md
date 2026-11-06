# Validation data

This directory is for data used in Phase 3. Nothing here is required for the synthetic benchmark.

## Input format

`ingest_incidents.py` accepts JSON Lines. Each line is one case plus the human decision:

```json
{
  "id": "incident-001",
  "at": "2026-10-01T12:00:00+00:00",
  "subject": "refund request",
  "options": [
    {"id": "auto-approve", "verb": "act", "name": "auto approve", "expected_benefit": 0.8},
    {"id": "ask", "verb": "ask", "name": "ask a human", "expected_benefit": 0.7}
  ],
  "human_action": "ask",
  "human_reason": "over the approval limit",
  "outcome": "helped",
  "context": {"amount": 780}
}
```

Required fields: `id`, `at`, `subject`, `options`, `human_action`.

## Privacy rules

- Remove names, emails, phone numbers, addresses, account ids and free text that can identify a person.
- Do not commit raw data. Commit only the anonymised file when it is legally safe.
- If the data cannot be published, write a data-access statement in
  `docs/05-project/novelty/validation.md`.
- The ingest script strips common PII keys recursively before writing.

## Commands

```bash
python scripts/novelty/ingest_incidents.py --input raw/incidents.jsonl
python scripts/novelty/analyze_validation.py
```

The first command writes `data/validation/anonymised/incidents-v1.jsonl`.
The second writes `data/validation/report.json` and prints agreement with the human decision.

## User study

`vignettes-v1.json` contains 20 vignettes with LAIX and utility-only recommendations. The protocol is
in `docs/05-project/novelty/user-study.md`. Collect results as JSON Lines, then run:

```bash
python scripts/novelty/analyze_user_study.py --input data/validation/user-study-results.jsonl
```

The analysis writes `data/validation/user-study-report.json`.
