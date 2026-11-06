# LAIX live bench — case format

This directory holds the live-bench case files. Each file is a list of
`DecisionProblem` scenarios in JSON. The Python loader converts them into
`LiveCase` objects for use with `run_live_bench()`.

## Current files

| File | Split | Cases |
|---|---|---:|
| `dev-cases-v1.json` | dev | 72 |
| `test-cases-v1.json` | test | 30 |
| `adversarial-cases-v1.json` | adversarial | 18 |

Regenerate the corpus with:

```bash
python scripts/novelty/generate_live_cases.py
```

## Schema

**`cases.v1.schema.json`** — JSON Schema (Draft 2020-12) for all case files in this
directory. Validate a file with:

```bash
# using python-jsonschema
python -m jsonschema -i my-cases.json benchmarks/live/cases.v1.schema.json
```

## File format

```json
{
  "schema": "laix/live-bench/v1",
  "version": "1.0.0",
  "split": "dev",
  "note": "Optional description.",
  "cases": [
    {
      "id": "my_case",
      "name": "My case",
      "tags": ["promise"],
      "expected_actions": ["safe"],
      "note": "Why safe is correct.",
      "problem": {
        "subject": "choose action",
        "at": "2026-11-01T10:00:00+00:00",
        "options": [
          {
            "id": "safe",
            "verb": "act",
            "name": "safe",
            "expected_benefit": 0.6
          },
          {
            "id": "risky",
            "verb": "act",
            "name": "risky",
            "expected_benefit": 0.9,
            "risk": 0.8,
            "reversible": false
          }
        ],
        "situation": {
          "id": "sit",
          "subject": "risk limit",
          "constraints": [
            { "id": "risk-limit", "kind": "risk", "value": 0.5, "hard": true }
          ]
        }
      }
    }
  ]
}
```

## Fields

### Top-level

| Field | Required | Description |
|---|---|---|
| `schema` | yes | Must be `"laix/live-bench/v1"`. |
| `version` | yes | Semver of this file (e.g. `"1.0.0"`). |
| `split` | yes | `"dev"`, `"test"`, or `"adversarial"`. |
| `note` | no | Free-text description. |
| `cases` | yes | Array of case objects. |

### Case

| Field | Required | Description |
|---|---|---|
| `id` | yes | Stable snake_case identifier, unique within the file. |
| `name` | yes | Short human-readable label shown in bench output. |
| `tags` | yes | At least one of: `promise`, `execution`, `attention`, `timing`, `conflict`, `plain`, `safety`. |
| `expected_actions` | yes | Action IDs the ideal planner should choose. Empty = run-only. |
| `note` | no | Explanation of why the expected action is correct. |
| `problem` | yes | The decision problem (see below). |

### Problem

| Field | Required | Description |
|---|---|---|
| `subject` | yes | What the task is about. |
| `at` | yes | ISO-8601 datetime with timezone. |
| `options` | yes | At least one option. |
| `situation` | no | Hard constraints (risk limit, cost limit, latency limit). |
| `commitments` | no | Open commitments that options may fulfill or violate. |
| `attention_budget` | no | `{ "total": float, "spent": float }`. |
| `approvals` | no | `{ "option_id": "approved" \| "rejected" \| "pending" }`. |

### Option

| Field | Required | Default | Description |
|---|---|---|---|
| `id` | yes | — | Unique within this problem. |
| `verb` | yes | — | One of the seven verbs. |
| `name` | yes | — | Human-readable label. |
| `expected_benefit` | no | `0.0` | Raw benefit estimate `[0, 1]`. |
| `cost` | no | `0.0` | Direct cost `≥ 0`. |
| `risk` | no | `0.0` | Probability × impact `[0, 1]`. |
| `interrupt_cost` | no | `0.0` | Fractional attention cost `[0, 1]`. |
| `latency_ms` | no | `0.0` | Expected execution latency. |
| `reversible` | no | `true` | `false` = irreversible action. |
| `requires_approval` | no | `false` | — |
| `commitments` | no | — | `{ "fulfills": [...], "violates": [...], "creates": [...] }` |
| `unknown_risk` | no | — | Fraction of risk that is unknown `[0, 1]`. |

## Target split sizes

The planned 120-case corpus:

| Tag | Count | Split dev / test / adversarial |
|---|---|---|
| promise | 20 | 12 / 5 / 3 |
| execution | 20 | 12 / 5 / 3 |
| attention | 20 | 12 / 5 / 3 |
| timing | 15 | 9 / 4 / 2 |
| conflict | 25 | 15 / 6 / 4 |
| plain | 20 | 12 / 5 / 3 |
| **total** | **120** | **72 / 30 / 18** |

Conflict cases carry two or more tags (promise + execution, promise + attention, etc.) but
are counted once in the conflict category.

## Loading cases in Python

```python
import json
from pathlib import Path
from laix import (
    ActionOption, AttentionBudget, Commitment, Constraint,
    DecisionProblem, Situation, run_live_bench, default_planners,
    LiveCase,
)


def load_cases(path: Path) -> list[LiveCase]:
    data = json.loads(path.read_text())
    cases = []
    for c in data["cases"]:
        p = c["problem"]

        situation = None
        if p.get("situation"):
            s = p["situation"]
            constraints = tuple(
                Constraint(id=co["id"], kind=co["kind"], value=co["value"], hard=co["hard"])
                for co in s.get("constraints", [])
            )
            situation = Situation(
                id=s["id"],
                at=p["at"],
                subject=s["subject"],
                constraints=constraints,
            )

        commitments = tuple(
            Commitment(
                id=cm["id"],
                subject=cm["subject"],
                due=cm.get("due"),
                priority=cm.get("priority", 0.0),
            )
            for cm in p.get("commitments", [])
        )

        attention_budget = None
        if p.get("attention_budget"):
            ab = p["attention_budget"]
            attention_budget = AttentionBudget(total=ab["total"], spent=ab["spent"])

        options = tuple(
            ActionOption(
                id=o["id"],
                verb=o["verb"],
                name=o["name"],
                expected_benefit=o.get("expected_benefit", 0.0),
                cost=o.get("cost", 0.0),
                risk=o.get("risk", 0.0),
                interrupt_cost=o.get("interrupt_cost", 0.0),
                latency_ms=o.get("latency_ms", 0.0),
                reversible=o.get("reversible", True),
                requires_approval=o.get("requires_approval", False),
                params={
                    **({"commitments": o["commitments"]} if o.get("commitments") else {}),
                    **({"unknown_risk": o["unknown_risk"]} if o.get("unknown_risk") is not None else {}),
                },
            )
            for o in p["options"]
        )

        attributes: dict = {}
        if commitments:
            attributes["commitments"] = commitments
        if attention_budget is not None:
            attributes["attention_budget"] = attention_budget
        if p.get("approvals"):
            attributes["approvals"] = p["approvals"]

        problem = DecisionProblem(
            subject=p["subject"],
            at=p["at"],
            situation=situation,
            options=options,
            attributes=attributes,
        )

        cases.append(
            LiveCase(
                name=c["id"],
                problem=problem,
                expected_actions=tuple(c.get("expected_actions", [])),
                tags=tuple(c.get("tags", [])),
            )
        )
    return cases


# Usage
cases = load_cases(Path("benchmarks/live/dev-cases-v1.json"))
report = run_live_bench(cases, default_planners())
print(report.summary())
```
