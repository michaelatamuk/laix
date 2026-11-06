# Incident replay

Input for the primary validation path: replay historical incidents through LAIX and compare the
chosen verb with what a human operator did.

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

`incidents-template.jsonl` is a filled example. The collection plan and field-mapping worksheet are
in [the collection kit](../../../docs/05-project/novelty/collection-kit.md).

## Privacy rules

- Remove names, emails, phone numbers, addresses, account ids and free text that can identify a person.
- Do not commit raw data. Commit only the anonymised file when it is legally safe.
- If the data cannot be published, write a data-access statement in
  [validation.md](../../../docs/05-project/novelty/validation.md).
- The ingest script strips common PII keys recursively before writing.

## Commands

```bash
python scripts/novelty/validation/check_validation_data.py --input raw/incidents.jsonl
python scripts/novelty/validation/ingest_incidents.py --input raw/incidents.jsonl
python scripts/novelty/validation/analyze_validation.py
```

The ingest command writes `data/validation/incidents/anonymised/incidents-v1.jsonl`.
The analysis writes `data/validation/incidents/report.json` and prints agreement with the human
decision.
