"""Analyse blinded user-study trials against the current recommendations."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "validation" / "user-study-results.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "validation" / "user-study-report.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]


def bootstrap_mean(values: list[float], *, seed: int, iterations: int = 10_000) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        total = 0.0
        for _ in range(len(values)):
            total += values[rng.randrange(len(values))]
        samples.append(total / len(values))
    samples.sort()
    return (
        round(samples[int(0.025 * iterations)], 6),
        round(samples[int(0.975 * iterations)], 6),
    )


def sign_test(differences: list[float]) -> tuple[int, int, float]:
    nonzero = [value for value in differences if value != 0]
    positive = sum(1 for value in nonzero if value > 0)
    negative = len(nonzero) - positive
    n = len(nonzero)
    if n == 0:
        return (0, 0, 1.0)
    k = min(positive, negative)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return (positive, negative, round(min(1.0, p), 6))


def fleiss_kappa(items: list[list[str]]) -> float | None:
    if not items:
        return None
    categories = sorted({value for item in items for value in item})
    total = 0
    p_items = []
    for item in items:
        n = len(item)
        if n < 2:
            continue
        counts = [item.count(value) for value in categories]
        p_items.append((sum(count * count for count in counts) - n) / (n * (n - 1)))
        total += n
    if not p_items or total == 0:
        return None
    p_bar = mean(p_items)
    p_e = sum((sum(1 for item in items for value in item if value == category) / total) ** 2 for category in categories)
    if p_e >= 1:
        return None
    return round((p_bar - p_e) / (1 - p_e), 6)


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"missing study data: {args.input}")
        print("The protocol is in docs/05-project/novelty/user-study.md")
        return 2

    rows = load_rows(args.input)
    if not rows:
        print("study file is empty")
        return 2

    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    ratings: dict[tuple[str, str, str], dict[str, float]] = {}
    choices: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        condition = str(row["condition"])
        by_condition[condition].append(row)
        key = (str(row["participant_id"]), str(row["vignette_id"]))
        ratings.setdefault(key, {})[condition] = float(row["trust"])
        choices[(str(row["vignette_id"]), condition)].append(str(row["choice"]))

    summary: dict[str, Any] = {
        "schema": "laix/user-study-report/v1",
        "participants": len({row["participant_id"] for row in rows}),
        "trials": len(rows),
        "conditions": {},
        "paired": {},
        "fleiss_kappa": {},
    }

    for condition in sorted(by_condition):
        selected = by_condition[condition]
        agreement = [1.0 if row["choice"] == row["recommendation"] else 0.0 for row in selected]
        summary["conditions"][condition] = {
            "trials": len(selected),
            "agreement": round(mean(agreement), 6),
            "agreement_ci": list(bootstrap_mean(agreement, seed=args.seed)),
            "mean_trust": round(mean(float(row["trust"]) for row in selected), 6),
            "mean_timeliness": round(mean(float(row["timeliness"]) for row in selected), 6),
            "mean_workload": round(mean(float(row["workload"]) for row in selected), 6),
        }

    differences = [
        values["laix"] - values["baseline"]
        for values in ratings.values()
        if "laix" in values and "baseline" in values
    ]
    positive, negative, p_value = sign_test(differences)
    summary["paired"] = {
        "pairs": len(differences),
        "mean_trust_delta": round(mean(differences), 6) if differences else 0.0,
        "delta_ci": list(bootstrap_mean(differences, seed=args.seed + 1)),
        "positive": positive,
        "negative": negative,
        "sign_test_p": p_value,
    }

    for (vignette, condition), values in sorted(choices.items()):
        kappa = fleiss_kappa([values])
        if kappa is not None:
            summary["fleiss_kappa"][f"{vignette}:{condition}"] = kappa

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"{'condition':<10} {'trials':>7} {'agreement':>10} {'trust':>8} {'timeliness':>11} {'workload':>9}")
    print("-" * 62)
    for condition in sorted(summary["conditions"]):
        item = summary["conditions"][condition]
        print(
            f"{condition:<10} {item['trials']:>7} {item['agreement']:>10.2%} "
            f"{item['mean_trust']:>8.2f} {item['mean_timeliness']:>11.2f} "
            f"{item['mean_workload']:>9.2f}"
        )
    print(
        f"\npaired trust delta: {summary['paired']['mean_trust_delta']:+.3f} "
        f"(95% CI {summary['paired']['delta_ci'][0]:+.3f} to {summary['paired']['delta_ci'][1]:+.3f}, "
        f"sign-test p={summary['paired']['sign_test_p']:.4f})"
    )
    try:
        shown = args.output.relative_to(ROOT)
    except ValueError:
        shown = args.output
    print(f"wrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
