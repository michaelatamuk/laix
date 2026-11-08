"""Check CABB optimality against brute force on small deterministic scenarios."""

from __future__ import annotations

import itertools
import json
import random
from pathlib import Path

from laix import (
    ActionOption,
    CABBPlanner,
    Commitment,
    DecisionScenario,
    DecisionStep,
    HumanAttentionBudget,
    RolloutPlanner,
)

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results" / "algorithm-directions" / "cabb.json"


def _scenario(seed: int) -> DecisionScenario:
    rng = random.Random(seed)
    steps = []
    for index in range(4):
        options = []
        for option_index in range(3):
            params: dict = {}
            if index == 0 and option_index == 0:
                params = {"commitments": {"fulfills": ["c1"]}}
            elif index == 0 and option_index == 1:
                params = {"commitments": {"violates": ["c1"]}}
            options.append(
                ActionOption(
                    id=f"s{index}o{option_index}",
                    verb="act" if option_index == 0 else "ask",
                    name=f"option {index}-{option_index}",
                    expected_benefit=rng.choice((0.4, 0.7, 0.9)),
                    risk=rng.choice((0.0, 0.2, 0.5)),
                    interrupt_cost=rng.choice((0.0, 0.2, 0.4)),
                    params=params,
                )
            )
        steps.append(
            DecisionStep(
                at=f"2026-11-01T{10 + index:02d}:00:00+00:00",
                options=tuple(options),
            )
        )
    return DecisionScenario(
        steps=tuple(steps),
        commitments=(
            Commitment(
                id="c1",
                subject="keep the promise",
                due="2026-11-01T09:00:00+00:00",
                priority=0.8,
            ),
        ),
        human_attention_budget=HumanAttentionBudget(total=2.0, spent=0.0),
    )


def _greedy_trap() -> DecisionScenario:
    """A cheap first step that blocks a better option under a shared budget."""
    return DecisionScenario(
        steps=(
            DecisionStep(
                at="2026-11-01T10:00:00+00:00",
                options=(ActionOption(id="start", verb="wait", name="start", expected_benefit=0.0),),
            ),
            DecisionStep(
                at="2026-11-01T10:10:00+00:00",
                options=(
                    ActionOption(id="big", verb="act", name="big", expected_benefit=1.0, interrupt_cost=0.9),
                    ActionOption(id="small", verb="act", name="small", expected_benefit=0.6, interrupt_cost=0.3),
                ),
            ),
            DecisionStep(
                at="2026-11-01T10:20:00+00:00",
                options=(
                    ActionOption(id="bonus", verb="act", name="bonus", expected_benefit=1.0, interrupt_cost=0.6),
                    ActionOption(id="nothing", verb="wait", name="nothing", expected_benefit=0.1),
                ),
            ),
        ),
        human_attention_budget=HumanAttentionBudget(total=1.0, spent=0.0),
    )


def _brute_force(planner: CABBPlanner, scenario: DecisionScenario) -> tuple[float, tuple[str, ...], int]:
    best = float("-inf")
    best_actions: tuple[str, ...] = ()
    evaluations = 0
    choices = [tuple(option.id for option in step.options) for step in scenario.steps]
    for actions in itertools.product(*choices):
        try:
            result = planner.evaluate(scenario, actions)
        except ValueError:
            continue
        evaluations += 1
        if result.score > best:
            best = result.score
            best_actions = actions
    return best, best_actions, evaluations


def main() -> int:
    planner = CABBPlanner()
    rollout = RolloutPlanner(planner)
    rows = []
    matches = 0
    rollout_matches = 0
    total_nodes = 0
    total_evaluations = 0
    for seed in range(12):
        scenario = _scenario(seed)
        plan = planner.plan(scenario)
        approximate = rollout.plan(scenario)
        best, best_actions, evaluations = _brute_force(planner, scenario)
        matches += int(abs(plan.score - best) <= 1e-6 and plan.actions == best_actions)
        rollout_matches += int(
            abs(approximate.score - best) <= 1e-6 and approximate.actions == best_actions
        )
        total_nodes += plan.nodes
        total_evaluations += evaluations
        rows.append(
            {
                "seed": seed,
                "cabb": {"actions": list(plan.actions), "score": plan.score, "nodes": plan.nodes},
                "rollout": {
                    "actions": list(approximate.actions),
                    "score": approximate.score,
                },
                "brute_force": {
                    "actions": list(best_actions),
                    "score": round(best, 6),
                    "evaluations": evaluations,
                },
            }
        )
    trap = _greedy_trap()
    exact_trap = planner.plan(trap)
    greedy_trap = rollout.plan(trap)
    payload = {
        "generated_by": "scripts/novelty/bench/run_cabb_bench.py",
        "status": "prototype",
        "scenarios": len(rows),
        "optimal_matches": matches,
        "rollout_matches": rollout_matches,
        "total_cabb_nodes": total_nodes,
        "total_brute_force_evaluations": total_evaluations,
        "greedy_trap": {
            "cabb": {"actions": list(exact_trap.actions), "score": exact_trap.score},
            "rollout": {"actions": list(greedy_trap.actions), "score": greedy_trap.score},
            "score_gap": round(exact_trap.score - greedy_trap.score, 6),
        },
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
