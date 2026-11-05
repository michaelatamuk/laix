"""A small training-free benchmark for live decisions.

The benchmark compares deterministic planners on cases that mix risk limits,
promises, execution risk and plain utility. It is intentionally small and
auditable: every case is a ``DecisionProblem`` and every row records the chosen
action, the expected action, safety, irreversibility, latency and score.
"""

from __future__ import annotations

import time
from typing import Iterable, Mapping

from ...decisions import ActionOption, Constraint, Situation
from ...planning import Commitment
from ..planners.attention.attention_planner import AttentionAwareEngine
from ..planners.commitment.commitment_planner import CommitmentAwareEngine
from ..contract.decision_engine import DecisionEngine
from ..contract.decision_problem import DecisionProblem
from ..planners.execution.execution_planner import ExecutionAwareEngine
from .first_option_engine import FirstOptionEngine
from .highest_benefit_engine import HighestBenefitEngine
from .live_bench_report import LiveBenchReport
from .live_bench_row import LiveBenchRow
from .live_case import LiveCase
from ..planners.live.live_engine import LiveDecisionEngine
from .planner_metrics import PlannerMetrics
from ..planners.utility.utility import UtilityEngine, _constraint_blocker


def default_planners() -> dict[str, DecisionEngine]:
    """The training-free planners and two naive baselines."""
    return {
        "first": FirstOptionEngine(),
        "benefit": HighestBenefitEngine(),
        "utility": UtilityEngine(),
        "commitment": CommitmentAwareEngine(),
        "execution": ExecutionAwareEngine(),
        "attention": AttentionAwareEngine(),
        "live": LiveDecisionEngine(),
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
