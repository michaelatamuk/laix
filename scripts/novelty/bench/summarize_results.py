"""Compare a fresh live-bench summary against the committed baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "results" / "live-bench" / "harness-v2"
DEFAULT_BASELINE = RESULTS / "baseline.json"
DEFAULT_CURRENT = RESULTS / "reports" / "summary.json"
TOLERANCE = 0.005
METRICS = ("accuracy", "promise_keeping", "irreversible_rate", "budget_violation_rate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--current", type=Path, default=DEFAULT_CURRENT)
    parser.add_argument("--tolerance", type=float, default=TOLERANCE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.baseline.exists():
        print(f"missing baseline: {args.baseline}")
        return 2
    if not args.current.exists():
        print(f"missing current summary: {args.current}")
        return 2

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    current = json.loads(args.current.read_text(encoding="utf-8"))
    failures = []

    print(f"{'planner':<22} {'metric':<22} {'baseline':>9} {'current':>9} {'delta':>9}")
    print("-" * 76)
    for planner in sorted(baseline.get("planners", {})):
        old = baseline["planners"][planner]
        new = current.get("planners", {}).get(planner)
        if new is None:
            failures.append(f"{planner}: missing from current summary")
            continue
        for metric in METRICS:
            before = float(old.get(metric, 0.0))
            after = float(new.get(metric, 0.0))
            delta = after - before
            if abs(delta) > args.tolerance:
                failures.append(f"{planner}.{metric}: {before:.4f} -> {after:.4f}")
            print(
                f"{planner:<22} {metric:<22} {before:>9.4f} {after:>9.4f} {delta:>+9.4f}"
            )

    print()
    if failures:
        print("FAIL: headline metrics moved beyond tolerance")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("OK: headline metrics match the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
