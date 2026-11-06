"""Paired significance tests and per-category breakdown for the live bench."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "results" / "live_bench_v2" / "raw.jsonl"
OUT = ROOT / "results" / "live_bench_v2" / "analysis.json"
REFERENCE = "live"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _p_value(chi2: float) -> float:
    return math.erfc(math.sqrt(max(0.0, chi2) / 2.0))


def mcnemar(live: dict[str, bool], other: dict[str, bool]) -> dict[str, float]:
    shared = sorted(set(live) & set(other))
    b = sum(1 for case in shared if live[case] and not other[case])
    c = sum(1 for case in shared if not live[case] and other[case])
    if b + c == 0:
        chi2 = 0.0
        p = 1.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        p = _p_value(chi2)
    return {
        "checked": len(shared),
        "live_only_correct": b,
        "other_only_correct": c,
        "chi2": round(chi2, 6),
        "p_value": round(p, 6),
    }


def cohens_h(p1: float, p2: float) -> float:
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def paired_bootstrap(
    live: dict[str, bool],
    other: dict[str, bool],
    *,
    iterations: int = 10_000,
    seed: int = 42,
) -> tuple[float, float, float]:
    shared = sorted(set(live) & set(other))
    if not shared:
        return (0.0, 0.0, 0.0)
    diffs = [int(live[case]) - int(other[case]) for case in shared]
    observed = sum(diffs) / len(diffs)
    rng = random.Random(seed)
    samples = []
    size = len(diffs)
    for _ in range(iterations):
        total = 0
        for _ in range(size):
            total += diffs[rng.randrange(size)]
        samples.append(total / size)
    samples.sort()
    low = samples[int(0.025 * iterations)]
    high = samples[min(iterations - 1, int(0.975 * iterations))]
    return (round(observed, 6), round(low, 6), round(high, 6))


def category_breakdown(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for tag in row["tags"]:
            buckets[tag][row["planner"]].append(row)
    result: dict[str, dict[str, Any]] = {}
    for tag, planners in sorted(buckets.items()):
        result[tag] = {}
        for planner, selected in sorted(planners.items()):
            checked = [row for row in selected if row["correct"] is not None]
            result[tag][planner] = {
                "cases": len(selected),
                "accuracy": round(
                    sum(1 for row in checked if row["correct"]) / len(checked), 6
                )
                if checked
                else 0.0,
                "promise_keeping": round(
                    sum(1 for row in selected if row["promise_kept"]) / len(selected), 6
                )
                if selected
                else 0.0,
                "irreversible_rate": round(
                    sum(1 for row in selected if row["irreversible"]) / len(selected), 6
                )
                if selected
                else 0.0,
                "budget_violation_rate": round(
                    sum(1 for row in selected if row["budget_violation"]) / len(selected), 6
                )
                if selected
                else 0.0,
            }
    return result


def main() -> int:
    args = parse_args()
    rows = load_rows(args.raw)
    planners = sorted({row["planner"] for row in rows})
    if REFERENCE not in planners:
        print(f"missing reference planner {REFERENCE!r}")
        return 2

    by_planner: dict[str, dict[str, bool]] = defaultdict(dict)
    for row in rows:
        if row["correct"] is not None:
            by_planner[row["planner"]][row["case"]] = bool(row["correct"])

    live = by_planner[REFERENCE]
    comparisons = {}
    for planner in planners:
        if planner == REFERENCE:
            continue
        other = by_planner[planner]
        stats = mcnemar(live, other)
        delta, low, high = paired_bootstrap(live, other, seed=args.seed)
        stats.update(
            {
                "live_accuracy": round(sum(live.values()) / len(live), 6) if live else 0.0,
                "other_accuracy": round(sum(other.values()) / len(other), 6) if other else 0.0,
                "accuracy_delta": delta,
                "delta_ci": [low, high],
                "cohens_h": round(
                    cohens_h(
                        sum(live.values()) / len(live) if live else 0.0,
                        sum(other.values()) / len(other) if other else 0.0,
                    ),
                    6,
                ),
            }
        )
        comparisons[f"{REFERENCE}_vs_{planner}"] = stats

    payload = {
        "schema": "laix/live-bench-analysis/v1",
        "seed": args.seed,
        "cases": len({row["case"] for row in rows}),
        "comparisons": comparisons,
        "categories": category_breakdown(rows),
    }
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Paired accuracy comparison against live")
    header = (
        f"{'planner':<12} {'delta':>8} {'95% CI':>15} {'b':>4} {'c':>4} "
        f"{'chi2':>8} {'p':>8} {'h':>8}"
    )
    print(header)
    print("-" * len(header))
    for name, item in comparisons.items():
        other = name.removeprefix(f"{REFERENCE}_vs_")
        ci = f"{item['delta_ci'][0]:.3f}-{item['delta_ci'][1]:.3f}"
        print(
            f"{other:<12} {item['accuracy_delta']:>8.3f} {ci:>15} "
            f"{item['live_only_correct']:>4} {item['other_only_correct']:>4} "
            f"{item['chi2']:>8.3f} {item['p_value']:>8.4f} {item['cohens_h']:>8.3f}"
        )
    print(f"\nwrote {args.out.relative_to(args.out.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
