# Validation collection kit

Decision: **incident replay first**, with the **user study as the fallback**.

Why this order:

- incident replay uses decisions that real people already made;
- it needs no recruitment or scheduling;
- it maps directly to `scripts/ingest_incidents.py` and `scripts/analyze_validation.py`;
- it gives reviewers the strongest evidence short of a live deployment.

Use the user study only if you cannot get incident data within two working days.

## Target

- Collect **200 raw cases**.
- Filter to **80–120 usable cases**.
- Aim for **at least 40 cases where LAIX and the human disagree**.
- If you reach 40 discordant cases earlier, stop; more data is better but not required for the first report.

## Where to look

Pick one source with a recorded human action:

- support tickets with a resolution or escalation;
- operations incidents with an action and an owner;
- refund or approval queues with approve/reject/ask;
- security alerts with triage decisions;
- delivery or scheduling exceptions with a chosen action;
- account or subscription actions with a recorded outcome.

Do not mix sources for the first study. One source keeps the result interpretable.

## What one case needs

| Field | Meaning | Example |
|---|---|---|
| `id` | Stable, non-personal case id | `case-0001` |
| `at` | Decision timestamp | `2026-10-01T12:00:00+00:00` |
| `subject` | Short category, not free text | `refund request` |
| `options` | Actions that were available | `approve`, `ask`, `wait` |
| `human_action` | What the person actually did | `ask` |
| `human_reason` | Reason code, not free text | `over_approval_limit` |
| `outcome` | Measured result if available | `helped` |
| `context` | Structured, non-personal inputs | `{"amount": 780}` |

`options` must be the actions that were actually available. If the source did not record them,
reconstruct them with the policy owner and mark the case `"options_reconstructed": true`.

## Mapping worksheet

| Source field | Maps to | Rule |
|---|---|---|
| ticket id | `id` | hash or renumber; never use a customer id |
| created time | `at` | ISO-8601 with timezone |
| category | `subject` | short label, no free text |
| resolution / action | `human_action` | must match one option id |
| reason code | `human_reason` | use the code, not the comment |
| measured result | `outcome` | `helped`, `neutral`, `hurt` or omit |
| amount / priority / risk | `context` | numbers or short enums only |
| names, emails, notes | — | **drop** |

## Seven-day plan

### Day 1 — source and sample

- pick one source;
- export 200 raw cases;
- confirm it has a recorded human action;
- write the mapping table for that source.

### Day 2 — pilot 20 cases

- map 20 cases by hand;
- run the preflight checker;
- run the analysis on the pilot;
- inspect the disagreements with the policy owner.

Stop here and switch to the user study if the source has no reliable human action.

### Day 3–4 — map the rest

- map 80–120 cases;
- keep a rejection log: why a case was excluded;
- anonymise names, emails, ids and free text;
- validate every row.

### Day 5 — run the analysis

```bash
python scripts/check_validation_data.py --input data/validation/anonymised/incidents-v1.jsonl
python scripts/analyze_validation.py --input data/validation/anonymised/incidents-v1.jsonl
```

Record:

- agreement with the human;
- discordant count;
- promise keeping, irreversible actions and budget violations where the fields exist;
- LAIX vs glue vs utility;
- failure examples.

### Day 6 — write the result

Fill the study record in `validation.md`:

- chosen option and why;
- data source and exclusions;
- sample size;
- agreement and confidence interval;
- discordant cases;
- limitations.

### Day 7 — update the paper

Replace the “validation pending” section of `paper-draft.md` with the real numbers.

## Inclusion rules

Include a case when:

- a person made one decision;
- at least two actions were available;
- the chosen action is recorded;
- the time is recorded;
- the case is safe to anonymise.

Exclude a case when:

- the decision is missing or ambiguous;
- the options cannot be reconstructed;
- the case is a duplicate;
- the case contains unremovable personal data;
- the decision was automatic and no human was involved (unless that is the comparison).

## Quality checks

- every `id` is unique;
- every `human_action` is one of the `options`;
- no option is empty;
- no PII keys remain;
- at least 40 discordant cases after the analysis;
- the rejection log explains every excluded case.

## Fallback: user study

If incident data is not available by day 2:

- use `data/validation/vignettes-v1.json` (20 vignettes);
- recruit 20–30 colleagues;
- each session is about 20–30 minutes;
- follow `user-study.md` and record results as JSONL;
- run `scripts/analyze_user_study.py`.

Consent and recruitment text are in `user-study-consent.md` and `user-study-recruitment.md`.

## What to send me first

Send a **20-row pilot** in the JSONL format. I will:

- check the mapping;
- run the analysis;
- point out ambiguous cases;
- adjust the mapping before you spend time on the full set.

Do not send raw tickets. Send only the anonymised pilot.

## Privacy

- Do not commit raw data.
- Keep raw exports outside the repository.
- Commit only the anonymised file when legally allowed.
- If the data cannot be published, write the access statement in `validation.md`.
