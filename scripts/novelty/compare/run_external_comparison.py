"""Run the optional external comparison adapters on one benchmark split."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NOVELTY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(NOVELTY))

from shared.live_bench_common import RESULTS, load_cases, split_paths

from benchmarks.compare import AdapterResult, LangGraphAdapter, TemporalAdapter

CAPABILITIES = ROOT / "benchmarks" / "compare" / "capabilities.v1.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--split",
        choices=("dev", "test", "adversarial", "all"),
        default="test",
    )
    return parser.parse_args()


def documented_only(name: str, reason: str) -> AdapterResult:
    return AdapterResult(
        name=name,
        available=False,
        dependencies=(reason,),
        notes=("documented capability comparison only",),
    )


def main() -> int:
    args = parse_args()
    cases = load_cases(split_paths(args.split))
    problems = [case.problem for case in cases]

    adapters = [
        LangGraphAdapter(),
        TemporalAdapter(),
    ]
    results = []
    for adapter in adapters:
        if adapter.available():
            results.append(adapter.run(problems))
        else:
            results.append(
                AdapterResult(
                    name=adapter.name,
                    available=False,
                    dependencies=adapter.dependencies,
                    notes=("optional dependency is not installed",),
                )
            )

    results.extend(
        [
            documented_only("pagerduty", "PagerDuty account"),
            documented_only("camunda", "Camunda server"),
        ]
    )

    payload = {
        "schema": "laix/external-comparison/v1",
        "split": args.split,
        "cases": len(cases),
        "capabilities": json.loads(CAPABILITIES.read_text(encoding="utf-8")),
        "adapters": [item.to_dict() for item in results],
    }
    target = RESULTS / "reports" / "external-comparison.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"External comparison — {args.split} split, {len(cases)} cases")
    print(f"{'adapter':<12} {'available':>9} {'decisions':>9} {'interrupts':>10} {'mean ms':>9} {'glue':>6}")
    print("-" * 64)
    for item in results:
        print(
            f"{item.name:<12} {item.available!s:>9} {item.decisions:>9} "
            f"{item.interrupts:>10} {item.mean_latency_ms:>9.3f} {item.glue_lines:>6}"
        )
    print(f"\nwrote {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
