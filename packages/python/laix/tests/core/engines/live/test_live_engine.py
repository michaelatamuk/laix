"""The integrated live planner combines promises, execution and attention."""

from __future__ import annotations

from laix import (
    ActionOption,
    AttentionBudget,
    Commitment,
    DecisionProblem,
    LiveDecisionEngine,
    default_cases,
    run_live_bench,
)


def _problem(*options: ActionOption, **attributes: object) -> DecisionProblem:
    return DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes=dict(attributes),
    )


def test_combines_all_three_live_concerns() -> None:
    commitments = (
        Commitment(
            id="c1",
            subject="send the report",
            due="2026-11-01T09:00:00+00:00",
        ),
    )
    plan = LiveDecisionEngine().solve(
        _problem(
            ActionOption(
                id="fast",
                verb="act",
                name="fast",
                expected_benefit=1.0,
                reversible=False,
                interrupt_cost=0.6,
                params={"commitments": {"violates": ["c1"]}},
            ),
            ActionOption(
                id="safe",
                verb="act",
                name="safe",
                expected_benefit=0.6,
                params={"commitments": {"fulfills": ["c1"]}},
            ),
            commitments=commitments,
        )
    )

    assert plan.action_id == "safe"
    assert plan.reason_code == "live_decision"
    assert plan.attributes["commitments_fulfilled"] == ["c1"]
    assert plan.attributes["utility"] == 0.6
    assert plan.attributes["commitment_score"] > 0
    assert plan.attributes["execution_score"] == 0.0


def test_blocks_a_rejected_approval() -> None:
    plan = LiveDecisionEngine().solve(
        _problem(
            ActionOption(id="rejected", verb="act", name="rejected", expected_benefit=0.9),
            ActionOption(id="direct", verb="act", name="direct", expected_benefit=0.6),
            approvals={"rejected": "rejected"},
        )
    )

    assert plan.action_id == "direct"


def test_respects_the_attention_budget() -> None:
    plan = LiveDecisionEngine().solve(
        _problem(
            ActionOption(id="ask", verb="ask", name="ask", expected_benefit=0.9),
            ActionOption(id="act", verb="act", name="act", expected_benefit=0.6),
            attention_budget=AttentionBudget(total=1.0, spent=0.9),
        )
    )

    assert plan.action_id == "act"


def test_wins_every_benchmark_case() -> None:
    report = run_live_bench(
        default_cases(),
        {"live": LiveDecisionEngine()},
    )

    assert report.metrics[0].accuracy == 1.0
    assert report.metrics[0].safety_violations == 0


def test_no_options_waits() -> None:
    plan = LiveDecisionEngine().solve(_problem())

    assert plan.verb == "wait"
    assert plan.reason_code == "no_options"
