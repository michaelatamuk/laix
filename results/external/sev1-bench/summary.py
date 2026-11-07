"""Summarise Sev1-Bench baseline vs LAIX results."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

print(f"scenarios: {len(rows)}")
print()
print("scenario                         cat              baseline  chooser  guard  root  rem")
print("-" * 92)
for row in rows:
    b = row["baseline_score"]
    c = row["laix_score"]
    g = row["guardrail_score"]
    cat = row["task"].get("category", "?")
    print(
        f"{row['scenario']:<32} {cat:<16} {b['total']:>8.2f} {c['total']:>8.2f} {g['total']:>6.2f}  "
        f"{int(g['root_cause_correct'])}     {int(g['remediation_correct'])}"
    )

print()
for label, key in (
    ("baseline", "baseline_score"),
    ("chooser", "laix_score"),
    ("guardrail", "guardrail_score"),
):
    scores = [r[key]["total"] for r in rows]
    passed = sum(1 for r in rows if r[key]["passed"])
    root = sum(1 for r in rows if r[key]["root_cause_correct"])
    rem = sum(1 for r in rows if r[key]["remediation_correct"])
    forb = sum(1 for r in rows if r[key]["forbidden_recommended"])
    print(
        f"{label:<9} mean {sum(scores)/len(scores):.3f}  pass {passed}/{len(rows)}  "
        f"root {root}/{len(rows)}  remediation {rem}/{len(rows)}  forbidden {forb}/{len(rows)}"
    )

print()
by_cat: dict[str, list[dict[str, object]]] = defaultdict(list)
for row in rows:
    by_cat[row["task"].get("category", "?")].append(row)
for cat, items in sorted(by_cat.items()):
    b = sum(r["baseline_score"]["total"] for r in items) / len(items)
    c = sum(r["laix_score"]["total"] for r in items) / len(items)
    g = sum(r["guardrail_score"]["total"] for r in items) / len(items)
    print(f"{cat:<18} n={len(items):>2}  baseline {b:.3f}  chooser {c:.3f}  guardrail {g:.3f}")

print()
print("scenarios where the chooser changed the answer:")
for row in rows:
    if row["baseline_action"].split(".")[0] != row["laix_action"].split(".")[0]:
        print(f"- {row['scenario']}: {row['laix_score']['total'] - row['baseline_score']['total']:+.2f}")
        print(f"  baseline: {row['baseline_action'][:140]}")
        print(f"  laix:     {row['laix_action'][:140]}")
