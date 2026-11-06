"""Compare LAIX, glue code and utility-only against recorded human decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from laix import LiveDecisionEngine, UtilityEngine
from shared.glue_baseline import GlueBaseline
from shared.live_bench_common import bootstrap_ci, build_problem, run_planner

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT / "data" / "incident-replay" / "output" / "anonymised.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "incident-replay" / "output" / "report.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"missing validation data: {args.input}")
        print("Create the file with scripts/novelty/incident-replay/ingest_incidents.py from a real export.")
        return 2

    rows = load_rows(args.input)
    if not rows:
        print("validation file is empty")
        return 2

    planners = {
        "live": LiveDecisionEngine(),
        "glue": GlueBaseline(),
        "utility": UtilityEngine(),
    }
    results: list[dict[str, Any]] = []
    for payload in rows:
        problem = build_problem(payload)
        human = str(payload["human_action"])
        for name, engine in planners.items():
            plan, latency = run_planner(engine, problem)
            results.append(
                {
                    "case": payload["id"],
                    "planner": name,
                    "human_action": human,
                    "chosen_action": plan.action_id,
                    "agree": plan.action_id == human,
                    "latency_ms": round(latency, 6),
                }
            )

    summary: dict[str, Any] = {
        "schema": "laix/validation-report/v1",
        "cases": len(rows),
        "seed": args.seed,
        "planners": {},
        "discordant": [
            item
            for item in results
            if item["planner"] == "live" and not item["agree"]
        ],
    }
    for name in planners:
        selected = [item for item in results if item["planner"] == name]
        flags = [bool(item["agree"]) for item in selected]
        low, high = bootstrap_ci([1.0 if flag else 0.0 for flag in flags], seed=args.seed)
        summary["planners"][name] = {
            "cases": len(selected),
            "agree": sum(1 for flag in flags if flag),
            "agreement": round(sum(1 for flag in flags if flag) / len(flags), 6),
            "agreement_ci": [low, high],
            "mean_latency_ms": round(
                sum(float(item["latency_ms"]) for item in selected) / len(selected), 6
            ),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"{'planner':<10} {'agreement':>10} {'95% CI':>15} {'agree':>7} {'cases':>6}")
    print("-" * 55)
    for name in sorted(summary["planners"]):
        item = summary["planners"][name]
        ci = f"{item['agreement_ci'][0]:.3f}-{item['agreement_ci'][1]:.3f}"
        print(
            f"{name:<10} {item['agreement']:>10.2%} {ci:>15} "
            f"{item['agree']:>7} {item['cases']:>6}"
        )
    try:
        try:
            shown = args.output.resolve().relative_to(ROOT)
        except ValueError:
            shown = args.output
    except ValueError:
        shown = args.output
    print(f"\nwrote {shown}")
    if summary["discordant"]:
        print(f"live disagrees on {len(summary['discordant'])} case(s):")
        for item in summary["discordant"][:10]:
            print(
                f"  - {item['case']}: live={item['chosen_action']} human={item['human_action']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
