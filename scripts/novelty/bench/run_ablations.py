"""Run the six live-planner ablations on one benchmark split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from laix import (
    AttentionWeights,
    CommitmentWeights,
    ExecutionWeights,
    LiveDecisionEngine,
    UtilityEngine,
)
from live_bench_common import (
    RESULTS,
    evaluate_case,
    load_cases,
    run_planner,
    split_paths,
    summarize,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split",
        choices=("dev", "test", "adversarial", "all"),
        default="test",
        help="Case split to run (default: test).",
    )
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def engines() -> dict[str, object]:
    zero_commitment = CommitmentWeights(
        keep=0.0, violate=0.0, create=0.0, due=0.0, blocked=0.0
    )
    zero_execution = ExecutionWeights(
        irreversible=0.0, unknown=0.0, approval=0.0, recovery=0.0
    )
    zero_attention = AttentionWeights(
        interrupt=0.0, approval=0.0, escalation=0.0, exhausted=0.0
    )
    equal_commitment = CommitmentWeights(
        keep=1.0, violate=1.0, create=1.0, due=1.0, blocked=1.0
    )
    equal_execution = ExecutionWeights(
        irreversible=1.0, unknown=1.0, approval=1.0, recovery=1.0
    )
    equal_attention = AttentionWeights(
        interrupt=1.0, approval=1.0, escalation=1.0, exhausted=1.0
    )
    return {
        "full": LiveDecisionEngine(),
        "no_commitment": LiveDecisionEngine(commitment_weights=zero_commitment),
        "no_execution": LiveDecisionEngine(execution_weights=zero_execution),
        "no_attention": LiveDecisionEngine(attention_weights=zero_attention),
        "utility_only": UtilityEngine(),
        "equal_weights": LiveDecisionEngine(
            commitment_weights=equal_commitment,
            execution_weights=equal_execution,
            attention_weights=equal_attention,
        ),
        "no_feasibility_gates": LiveDecisionEngine(enforce_feasibility=False),
    }


def main() -> int:
    args = parse_args()
    cases = load_cases(split_paths(args.split))
    rows = []
    for name, engine in engines().items():
        for case in cases:
            plan, latency = run_planner(engine, case.problem)
            rows.append(
                evaluate_case(
                    case,
                    name,
                    plan,
                    latency,
                    split=args.split,
                    seed=args.seed,
                )
            )

    summary = summarize(rows, split=args.split, seed=args.seed)
    RESULTS.mkdir(parents=True, exist_ok=True)
    target = RESULTS / "ablations.json"
    target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    header = (
        f"{'variant':<22} {'acc':>7} {'promise':>8} {'irrev':>7} {'budget':>7}"
    )
    print(header)
    print("-" * len(header))
    for name in sorted(summary["planners"]):
        item = summary["planners"][name]
        print(
            f"{name:<22} {item['accuracy']:>7.2%} {item['promise_keeping']:>8.2%} "
            f"{item['irreversible_rate']:>7.2%} {item['budget_violation_rate']:>7.2%}"
        )
    print(f"\nwrote {target.relative_to(target.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
