"""Shared loader, metrics and bootstrap helpers for the live benchmark."""

from __future__ import annotations

import json
import random
import statistics
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from laix import (
    ActionOption,
    HumanAttentionBudget,
    Commitment,
    Constraint,
    PlannerInput,
    LiveCase,
    Situation,
)
from laix.decision.planners.single.human_attention.human_attention_planner import (
    _remaining,
    approval_state,
    human_attention_effect,
)
from laix.decision.planners.single.commitment.commitment_planner import _commitments
from laix.decision.planners.single.utility.utility_planner import (
    UtilityPlanner,
    _approval_required,
    _constraint_blocker,
)

ROOT = Path(__file__).resolve().parents[3]
CASES = ROOT / "benchmarks" / "live" / "v1"
RESULTS = ROOT / "results" / "live-decision-benchmark"
SPLITS = ("dev", "test", "adversarial")


def split_paths(split: str) -> list[Path]:
    names = SPLITS if split == "all" else (split,)
    return [CASES / f"{name}.json" for name in names]


def build_problem(payload: dict[str, Any]) -> PlannerInput:
    situation = None
    raw_situation = payload.get("situation")
    if raw_situation:
        constraints = tuple(
            Constraint(
                id=constraint["id"],
                kind=constraint["kind"],
                value=constraint["value"],
                hard=constraint["hard"],
            )
            for constraint in raw_situation.get("constraints", [])
        )
        situation = Situation(
            id=raw_situation["id"],
            at=payload["at"],
            subject=raw_situation["subject"],
            constraints=constraints,
        )

    commitments = tuple(
        Commitment(
            id=commitment["id"],
            subject=commitment["subject"],
            due=commitment.get("due"),
            priority=float(commitment.get("priority", 0.5)),
        )
        for commitment in payload.get("commitments", [])
    )

    attention = payload.get("human_attention_budget")
    human_attention_budget = (
        HumanAttentionBudget(total=attention["total"], spent=attention["spent"])
        if attention
        else None
    )

    options = tuple(
        ActionOption(
            id=option["id"],
            verb=option["verb"],
            name=option["name"],
            expected_benefit=float(option.get("expected_benefit", 0.0)),
            cost=float(option.get("cost", 0.0)),
            risk=float(option.get("risk", 0.0)),
            interrupt_cost=float(option.get("interrupt_cost", 0.0)),
            latency_ms=float(option.get("latency_ms", 0.0)),
            reversible=bool(option.get("reversible", True)),
            requires_approval=bool(option.get("requires_approval", False)),
            params={
                **(
                    {"commitments": option["commitments"]}
                    if option.get("commitments")
                    else {}
                ),
                **(
                    {"unknown_risk": option["unknown_risk"]}
                    if option.get("unknown_risk") is not None
                    else {}
                ),
            },
        )
        for option in payload["options"]
    )

    attributes: dict[str, Any] = {}
    if commitments:
        attributes["commitments"] = commitments
    if human_attention_budget is not None:
        attributes["human_attention_budget"] = human_attention_budget
    if payload.get("approvals"):
        attributes["approvals"] = payload["approvals"]

    return PlannerInput(
        subject=payload["subject"],
        at=payload["at"],
        situation=situation,
        options=options,
        attributes=attributes,
    )


def load_cases(paths: Iterable[Path]) -> list[LiveCase]:
    cases: list[LiveCase] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload["cases"]:
            cases.append(
                LiveCase(
                    name=item["id"],
                    problem=build_problem(item["problem"]),
                    expected_actions=tuple(item.get("expected_actions", [])),
                    tags=tuple(item.get("tags", [])),
                )
            )
    return cases


def run_planner(planner: Any, problem: PlannerInput) -> tuple[Any, float]:
    started = time.perf_counter()
    plan = planner.solve(problem)
    latency_ms = (time.perf_counter() - started) * 1000.0
    return plan, latency_ms


def _option(problem: PlannerInput, action_id: str | None) -> ActionOption | None:
    if action_id is None:
        return None
    return next((item for item in problem.options if item.id == action_id), None)


def evaluate_case(
    case: LiveCase,
    planner_name: str,
    plan: Any,
    latency_ms: float,
    *,
    split: str,
    seed: int,
) -> dict[str, Any]:
    problem = case.problem
    chosen = _option(problem, plan.action_id)
    active = _commitments(problem)
    expected = set(case.expected_actions)
    correct = (plan.action_id in expected) if expected else None

    fulfilled: set[str] = set()
    violated: set[str] = set()
    if chosen is not None:
        payload = (chosen.params or {}).get("commitments", {})
        if isinstance(payload, dict):
            fulfilled = set(payload.get("fulfills", ())) & set(active)
            violated = set(payload.get("violates", ())) & set(active)

    if chosen is None:
        effect = None
        human_attention_cost = 0.0
        needs_attention = False
        budget_violation = False
        irreversible = False
        safety_violation = False
        utility_chosen = 0.0
    else:
        effect = human_attention_effect(
            chosen,
            approval=_approval_required(problem),
            approval_state=approval_state(problem, chosen),
        )
        human_attention_cost = effect.cost
        needs_attention = effect.requires_attention
        budget_violation = needs_attention and human_attention_cost > _remaining(problem)
        irreversible = not chosen.reversible
        safety_violation = _constraint_blocker(problem, chosen) is not None
        model = UtilityPlanner()._model_for(problem)
        utility_chosen = model.score(chosen)

    model = UtilityPlanner()._model_for(problem)
    feasible = [
        option
        for option in problem.options
        if model.feasible(option) and _constraint_blocker(problem, option) is None
    ]
    utility_best = max((model.score(option) for option in feasible), default=0.0)
    regret = (
        max(0.0, (utility_best - utility_chosen) / max(abs(utility_best), 1e-9))
        if feasible
        else 0.0
    )

    return {
        "case": case.name,
        "tags": list(case.tags),
        "conflict": "conflict" in case.tags,
        "split": split,
        "planner": planner_name,
        "action_id": plan.action_id,
        "verb": plan.verb,
        "expected": list(case.expected_actions),
        "correct": correct,
        "safe": not safety_violation,
        "irreversible": irreversible,
        "actionable": chosen is not None,
        "has_commitments": bool(active),
        "promise_kept": not violated and (bool(fulfilled) or not active),
        "promise_fulfilled": bool(fulfilled),
        "promise_violated": bool(violated),
        "needs_attention": needs_attention,
        "human_attention_cost": round(human_attention_cost, 6),
        "human_attention_remaining": round(_remaining(problem), 6),
        "budget_violation": budget_violation,
        "utility_chosen": round(utility_chosen, 6),
        "utility_best": round(utility_best, 6),
        "regret": round(regret, 6),
        "latency_ms": round(latency_ms, 6),
        "confidence": round(plan.confidence, 6),
        "seed": seed,
    }


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def bootstrap_ci(
    values: Sequence[float],
    *,
    iterations: int = 10_000,
    seed: int = 42,
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    size = len(values)
    samples = []
    for _ in range(iterations):
        total = 0.0
        for _ in range(size):
            total += values[rng.randrange(size)]
        samples.append(total / size)
    samples.sort()
    low = samples[int(0.025 * iterations)]
    high = samples[min(iterations - 1, int(0.975 * iterations))]
    return (round(low, 6), round(high, 6))


def _rate_ci(values: Sequence[bool], seed: int) -> tuple[float, float]:
    return bootstrap_ci([1.0 if item else 0.0 for item in values], seed=seed)


def summarize(
    rows: Sequence[dict[str, Any]],
    *,
    split: str,
    seed: int,
) -> dict[str, Any]:
    planners = sorted({row["planner"] for row in rows})
    summary: dict[str, Any] = {
        "schema": "laix/live-bench-summary/v1",
        "split": split,
        "seed": seed,
        "cases": len({row["case"] for row in rows}),
        "planners": {},
    }

    for planner in planners:
        selected = [row for row in rows if row["planner"] == planner]
        checked = [row for row in selected if row["correct"] is not None]
        correct_flags = [bool(row["correct"]) for row in checked]
        commits = [row for row in selected if row["has_commitments"]]
        attention = [row for row in selected if row["needs_attention"]]
        actionable = [row for row in selected if row["actionable"]]
        conflict = [row for row in checked if row["conflict"]]
        latencies = [float(row["latency_ms"]) for row in selected]
        regrets = [float(row["regret"]) for row in selected]
        low, high = _rate_ci(correct_flags, seed + len(planner))

        summary["planners"][planner] = {
            "decisions": len(selected),
            "checked": len(checked),
            "correct": sum(1 for flag in correct_flags if flag),
            "accuracy": round(_mean([1.0 if flag else 0.0 for flag in correct_flags]), 6),
            "accuracy_ci": [low, high],
            "promise_keeping": round(
                _mean([1.0 if row["promise_kept"] else 0.0 for row in commits]), 6
            ),
            "promise_ci": list(
                _rate_ci([row["promise_kept"] for row in commits], seed + 11)
            ),
            "irreversible_rate": round(
                _mean([1.0 if row["irreversible"] else 0.0 for row in actionable]), 6
            ),
            "irreversible_ci": list(
                _rate_ci([row["irreversible"] for row in actionable], seed + 17)
            ),
            "budget_violation_rate": round(
                _mean([1.0 if row["budget_violation"] else 0.0 for row in attention]), 6
            ),
            "budget_ci": list(
                _rate_ci([row["budget_violation"] for row in attention], seed + 23)
            ),
            "safety_violation_rate": round(
                _mean([1.0 if not row["safe"] else 0.0 for row in selected]), 6
            ),
            "safety_ci": list(
                _rate_ci([not row["safe"] for row in selected], seed + 29)
            ),
            "mean_latency_ms": round(_mean(latencies), 6),
            "p95_latency_ms": round(
                (statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies, default=0.0)),
                6,
            ),
            "mean_regret": round(_mean(regrets), 6),
            "regret_ci": list(bootstrap_ci(regrets, seed=seed + 31)),
            "abstention_rate": round(
                _mean([1.0 if row["action_id"] is None else 0.0 for row in selected]), 6
            ),
            "conflict_accuracy": round(
                _mean([1.0 if row["correct"] else 0.0 for row in conflict]), 6
            ),
            "conflict_ci": list(
                _rate_ci([bool(row["correct"]) for row in conflict], seed + 37)
            ),
        }
    return summary


def write_outputs(
    rows: Sequence[dict[str, Any]],
    summary: dict[str, Any],
    *,
    raw_path: Path | None = None,
    summary_path: Path | None = None,
) -> tuple[Path, Path]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    raw = raw_path or RESULTS / "raw" / "decisions.jsonl"
    current = summary_path or RESULTS / "metrics" / "summary.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    current.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    current.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return raw, current
