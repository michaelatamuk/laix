# Incident replay

Primary validation path: replay historical incidents through LAIX and compare the chosen verb with
what a human operator did.

## Inputs and outputs

| Path | Status | Contents |
|---|---|---|
| `template.jsonl` | committed | one filled example row |
| `raw/` | gitignored | your raw export |
| `output/anonymised.jsonl` | generated | PII-stripped rows |
| `output/report.json` | generated | agreement and discordance analysis |

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

`template.jsonl` is a filled example. The collection plan and field-mapping worksheet are in
[the collection kit](../../docs/05-project/novelty/collection-kit.md).

## Privacy rules

- Remove names, emails, phone numbers, addresses, account ids and free text that can identify a person.
- Do not commit raw data. `raw/` and `output/` are gitignored by default.
- Publish a reviewed anonymised file as a release artifact when it is legally safe.
- If the data cannot be published, write a data-access statement in
  [validation.md](../../docs/05-project/novelty/validation.md).
- The ingest script strips common PII keys recursively before writing.

## Commands

Put the raw export in `data/incident-replay/raw/` so the default paths stay meaningful:

```bash
python scripts/novelty/incident-replay/preflight_incidents.py --input data/incident-replay/raw/incidents.jsonl
python scripts/novelty/incident-replay/ingest_incidents.py --input data/incident-replay/raw/incidents.jsonl
python scripts/novelty/incident-replay/analyze_incident_replay.py
```

The ingest command writes `data/incident-replay/output/anonymised.jsonl`.
The analysis writes `data/incident-replay/output/report.json` and prints agreement with the human
decision.
