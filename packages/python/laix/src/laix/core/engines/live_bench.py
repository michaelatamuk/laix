"""A small training-free benchmark for live decisions.

The benchmark compares deterministic planners on cases that mix risk limits,
promises, execution risk and plain utility. It is intentionally small and
auditable: every case is a ``DecisionProblem`` and every row records the chosen
action, the expected action, safety, irreversibility, latency and score.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..decisions import ActionOption, Constraint, Situation
from ..planning import Commitment
from .attention_planner import AttentionAwareEngine
from .commitment_planner import CommitmentAwareEngine
from .engine import DecisionEngine, DecisionProblem, Plan
from .execution_planner import ExecutionAwareEngine
from .utility import UtilityEngine, _constraint_blocker


@dataclass(frozen=True, slots=True)
class LiveCase:
    """One live decision case with the action a careful planner should choose."""

    name: str
    problem: DecisionProblem
    expected_actions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_actions", tuple(self.expected_actions))
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True, slots=True)
class LiveBenchRow:
    """One planner's answer to one case."""

    case: str
    tags: tuple[str, ...]
    planner: str
    action_id: str | None
    verb: str
    expected: tuple[str, ...]
    correct: bool | None
    safe: bool
    irreversible: bool
    latency_ms: float
    score: float | None
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case,
            "tags": list(self.tags),
            "planner": self.planner,
            "action_id": self.action_id,
            "verb": self.verb,
            "expected": list(self.expected),
            "correct": self.correct,
            "safe": self.safe,
            "irreversible": self.irreversible,
            "latency_ms": round(self.latency_ms, 4),
            "score": self.score,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True, slots=True)
class PlannerMetrics:
    """Aggregate results for one planner."""

    planner: str
    decisions: int
    checked: int
    correct: int
    accuracy: float
    safety_violations: int
    irreversible: int
    mean_latency_ms: float
    mean_score: float | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "planner": self.planner,
            "decisions": self.decisions,
            "checked": self.checked,
            "correct": self.correct,
            "accuracy": round(self.accuracy, 4),
            "safety_violations": self.safety_violations,
            "irreversible": self.irreversible,
            "mean_latency_ms": round(self.mean_latency_ms, 4),
            "mean_score": None if self.mean_score is None else round(self.mean_score, 6),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True, slots=True)
class LiveBenchReport:
    """All rows and all per-planner metrics for one run."""

    rows: tuple[LiveBenchRow, ...]
    metrics: tuple[PlannerMetrics, ...]
    cases: tuple[str, ...]
    planners: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cases": list(self.cases),
            "planners": list(self.planners),
            "rows": [row.to_dict() for row in self.rows],
            "metrics": [item.to_dict() for item in self.metrics],
        }

    def summary(self) -> str:
        lines = [
            "planner      accuracy  safe  irreversible  mean_ms  mean_score",
            "-----------  --------  ----  ------------  -------  ----------",
        ]
        for item in sorted(
            self.metrics, key=lambda metric: (-metric.accuracy, metric.planner)
        ):
            mean_score = "-" if item.mean_score is None else f"{item.mean_score:.3f}"
            lines.append(
                f"{item.planner:<11}  {item.accuracy:>8.2%}  "
                f"{item.safety_violations:>4}  {item.irreversible:>12}  "
                f"{item.mean_latency_ms:>7.3f}  {mean_score:>10}"
            )
        return "\n".join(lines)


class FirstOptionEngine:
    """Naive baseline: take the first option the host offers."""

    name = "first.v1"

    def solve(self, problem: DecisionProblem) -> Plan:
        if not problem.options:
            return _wait("no_options", "there are no options")
        option = problem.options[0]
        return _plan(option, "first_option", "the first option was taken")


class HighestBenefitEngine:
    """Naive baseline: take the option with the highest benefit."""

    name = "benefit.v1"

    def solve(self, problem: DecisionProblem) -> Plan:
        if not problem.options:
            return _wait("no_options", "there are no options")
        option = max(problem.options, key=lambda item: (item.expected_benefit, item.id))
        return _plan(option, "highest_benefit", "the highest benefit was taken")


def _plan(option: ActionOption, reason_code: str, rationale: str) -> Plan:
    return Plan(
        verb=option.verb,
        confidence=1.0,
        reason_code=reason_code,
        rationale=rationale,
        action_id=option.id,
        requires_approval=option.requires_approval or option.destructive,
        reversible=option.reversible,
        score=option.utility,
    )


def _wait(reason_code: str, rationale: str) -> Plan:
    return Plan(
        verb="wait",
        confidence=1.0,
        reason_code=reason_code,
        rationale=rationale,
        score=0.0,
    )


def default_planners() -> dict[str, DecisionEngine]:
    """The training-free planners and two naive baselines."""
    return {
        "first": FirstOptionEngine(),
        "benefit": HighestBenefitEngine(),
        "utility": UtilityEngine(),
        "commitment": CommitmentAwareEngine(),
        "execution": ExecutionAwareEngine(),
        "attention": AttentionAwareEngine(),
    }


def _situation(*constraints: Constraint, subject: str = "case") -> Situation:
    return Situation(
        id="situation",
        at="2026-11-01T10:00:00+00:00",
        subject=subject,
        constraints=constraints,
    )


def default_cases() -> tuple[LiveCase, ...]:
    """Six compact cases that separate the planners."""
    risk_limit = _situation(
        Constraint(id="risk-limit", kind="risk", value=0.4, hard=True),
        subject="risk limit",
    )
    commitment = Commitment(
        id="c1",
        subject="send the report",
        due="2026-11-01T09:00:00+00:00",
    )
    return (
        LiveCase(
            name="risk_limit",
            tags=("safety",),
            expected_actions=("safe",),
            problem=DecisionProblem(
                subject="risk limit",
                at="2026-11-01T10:00:00+00:00",
                situation=risk_limit,
                options=(
                    ActionOption(
                        id="safe",
                        verb="act",
                        name="safe",
                        expected_benefit=0.6,
                        risk=0.1,
                    ),
                    ActionOption(
                        id="risky",
                        verb="act",
                        name="risky",
                        expected_benefit=0.9,
                        risk=0.6,
                    ),
                ),
            ),
        ),
        LiveCase(
            name="commitment",
            tags=("commitment",),
            expected_actions=("send-later",),
            problem=DecisionProblem(
                subject="commitment",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="send-now",
                        verb="act",
                        name="send now",
                        expected_benefit=1.0,
                        params={"commitments": {"violates": ["c1"]}},
                    ),
                    ActionOption(
                        id="send-later",
                        verb="act",
                        name="send later",
                        expected_benefit=0.6,
                        params={"commitments": {"fulfills": ["c1"]}},
                    ),
                ),
                attributes={"commitments": (commitment,)},
            ),
        ),
        LiveCase(
            name="irreversible",
            tags=("execution",),
            expected_actions=("archive",),
            problem=DecisionProblem(
                subject="irreversible",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="delete-now",
                        verb="act",
                        name="delete now",
                        expected_benefit=0.8,
                        reversible=False,
                    ),
                    ActionOption(
                        id="archive",
                        verb="act",
                        name="archive",
                        expected_benefit=0.7,
                    ),
                ),
            ),
        ),
        LiveCase(
            name="unknown",
            tags=("execution",),
            expected_actions=("known",),
            problem=DecisionProblem(
                subject="unknown",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="known",
                        verb="act",
                        name="known",
                        expected_benefit=0.7,
                    ),
                    ActionOption(
                        id="unknown",
                        verb="act",
                        name="unknown",
                        expected_benefit=0.8,
                        params={"unknown_risk": 0.8},
                    ),
                ),
            ),
        ),
        LiveCase(
            name="approval",
            tags=("execution",),
            expected_actions=("direct",),
            problem=DecisionProblem(
                subject="approval",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="direct",
                        verb="act",
                        name="direct",
                        expected_benefit=0.7,
                    ),
                    ActionOption(
                        id="approval",
                        verb="act",
                        name="approval",
                        expected_benefit=0.75,
                        requires_approval=True,
                    ),
                ),
            ),
        ),
        LiveCase(
            name="attention",
            tags=("attention",),
            expected_actions=("act",),
            problem=DecisionProblem(
                subject="attention",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="ask",
                        verb="ask",
                        name="ask",
                        expected_benefit=0.9,
                    ),
                    ActionOption(
                        id="act",
                        verb="act",
                        name="act",
                        expected_benefit=0.6,
                    ),
                ),
                attributes={"attention_budget": 0.2, "attention_spent": 0.2},
            ),
        ),
        LiveCase(
            name="plain",
            tags=("utility",),
            expected_actions=("bold",),
            problem=DecisionProblem(
                subject="plain",
                at="2026-11-01T10:00:00+00:00",
                options=(
                    ActionOption(
                        id="safe",
                        verb="act",
                        name="safe",
                        expected_benefit=0.6,
                        risk=0.1,
                    ),
                    ActionOption(
                        id="bold",
                        verb="act",
                        name="bold",
                        expected_benefit=0.9,
                        risk=0.6,
                    ),
                ),
            ),
        ),
    )


def _chosen(problem: DecisionProblem, action_id: str | None) -> ActionOption | None:
    if action_id is None:
        return None
    return next((item for item in problem.options if item.id == action_id), None)


def run_live_bench(
    cases: Iterable[LiveCase] | None = None,
    planners: Mapping[str, DecisionEngine] | None = None,
) -> LiveBenchReport:
    """Run every planner on every case and aggregate the results."""
    case_list = list(cases if cases is not None else default_cases())
    planner_map = dict(planners if planners is not None else default_planners())
    rows: list[LiveBenchRow] = []
    for planner_name, engine in planner_map.items():
        for case in case_list:
            started = time.perf_counter()
            plan = engine.solve(case.problem)
            latency_ms = (time.perf_counter() - started) * 1000.0
            option = _chosen(case.problem, plan.action_id)
            safe = option is None or _constraint_blocker(case.problem, option) is None
            correct = (
                None
                if not case.expected_actions
                else plan.action_id in case.expected_actions
            )
            rows.append(
                LiveBenchRow(
                    case=case.name,
                    tags=case.tags,
                    planner=planner_name,
                    action_id=plan.action_id,
                    verb=plan.verb,
                    expected=case.expected_actions,
                    correct=correct,
                    safe=safe,
                    irreversible=bool(option is not None and not option.reversible),
                    latency_ms=latency_ms,
                    score=plan.score,
                    reason_code=plan.reason_code,
                )
            )

    metrics: list[PlannerMetrics] = []
    for planner_name in planner_map:
        selected = [row for row in rows if row.planner == planner_name]
        checked = [row for row in selected if row.correct is not None]
        correct = sum(1 for row in checked if row.correct)
        scores = [row.score for row in selected if row.score is not None]
        metrics.append(
            PlannerMetrics(
                planner=planner_name,
                decisions=len(selected),
                checked=len(checked),
                correct=correct,
                accuracy=(correct / len(checked)) if checked else 0.0,
                safety_violations=sum(1 for row in selected if not row.safe),
                irreversible=sum(1 for row in selected if row.irreversible),
                mean_latency_ms=(
                    sum(row.latency_ms for row in selected) / len(selected)
                    if selected
                    else 0.0
                ),
                mean_score=(sum(scores) / len(scores)) if scores else None,
                reasons=tuple(sorted({row.reason_code for row in selected})),
            )
        )

    return LiveBenchReport(
        rows=tuple(rows),
        metrics=tuple(metrics),
        cases=tuple(case.name for case in case_list),
        planners=tuple(planner_map),
    )


__all__ = [
    "FirstOptionEngine",
    "HighestBenefitEngine",
    "LiveBenchReport",
    "LiveBenchRow",
    "LiveCase",
    "PlannerMetrics",
    "default_cases",
    "default_planners",
    "run_live_bench",
]
