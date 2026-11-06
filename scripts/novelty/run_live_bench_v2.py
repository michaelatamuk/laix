"""Run the 120-case live bench with metrics and bootstrap confidence intervals."""

from __future__ import annotations

import argparse
import sys

from glue_baseline import GlueBaseline
from laix import default_planners
from live_bench_common import (
    evaluate_case,
    load_cases,
    run_planner,
    split_paths,
    summarize,
    write_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split",
        choices=("dev", "test", "adversarial", "all"),
        default="all",
        help="Case split to run (default: all).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Bootstrap seed.")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Print results without writing results/live_bench_v2/.",
    )
    return parser.parse_args()


def print_table(summary: dict) -> None:
    header = (
        f"{'planner':<11} {'acc':>7} {'95% CI':>15} {'promise':>8} "
        f"{'irrev':>7} {'budget':>7} {'p95 ms':>8} {'regret':>8}"
    )
    print(header)
    print("-" * len(header))
    for name in sorted(summary["planners"]):
        item = summary["planners"][name]
        ci = f"{item['accuracy_ci'][0]:.2f}-{item['accuracy_ci'][1]:.2f}"
        print(
            f"{name:<11} {item['accuracy']:>7.2%} {ci:>15} "
            f"{item['promise_keeping']:>8.2%} {item['irreversible_rate']:>7.2%} "
            f"{item['budget_violation_rate']:>7.2%} {item['p95_latency_ms']:>8.3f} "
            f"{item['mean_regret']:>8.3f}"
        )


def print_conflict_table(summary: dict) -> None:
    print()
    print("Conflict cases")
    print(f"{'planner':<11} {'conflict acc':>13} {'95% CI':>15}")
    print("-" * 41)
    for name in sorted(summary["planners"]):
        item = summary["planners"][name]
        ci = f"{item['conflict_ci'][0]:.2f}-{item['conflict_ci'][1]:.2f}"
        print(f"{name:<11} {item['conflict_accuracy']:>13.2%} {ci:>15}")


def main() -> int:
    args = parse_args()
    paths = split_paths(args.split)
    missing = [path for path in paths if not path.exists()]
    if missing:
        print("Missing case files:", ", ".join(str(path) for path in missing), file=sys.stderr)
        print("Run: python scripts/generate_live_cases.py", file=sys.stderr)
        return 2

    cases = load_cases(paths)
    planners = {"glue": GlueBaseline(), **default_planners()}
    rows = []
    for planner_name, engine in planners.items():
        for case in cases:
            plan, latency = run_planner(engine, case.problem)
            rows.append(
                evaluate_case(
                    case,
                    planner_name,
                    plan,
                    latency,
                    split=args.split,
                    seed=args.seed,
                )
            )

    summary = summarize(rows, split=args.split, seed=args.seed)
    if not args.no_write:
        raw, current = write_outputs(rows, summary)
        print(f"wrote {raw.relative_to(raw.parents[2])}")
        print(f"wrote {current.relative_to(current.parents[2])}")
        print()

    print_table(summary)
    print_conflict_table(summary)

    live = summary["planners"].get("live")
    if live is None:
        return 2
    failed = live["conflict_accuracy"] < 1.0
    if failed:
        print("\nFAIL: the integrated planner did not win every conflict case.", file=sys.stderr)
        return 1
    print("\nOK: the integrated planner won every conflict case.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
