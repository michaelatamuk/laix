"""The planner contract and its policy adapter."""

from __future__ import annotations

from laix import (
    ActionOption,
    PlannerInput,
    DecisionRequest,
    PlannerPolicy,
    Intent,
    PlannerResult,
    to_decision,
    to_planner_input,
)


class FakePlanner:
    def solve(self, problem: PlannerInput) -> PlannerResult:
        assert problem.subject == "a task"
        assert problem.options[0].id == "a1"
        return PlannerResult(
            verb="act",
            confidence=0.91,
            reason_code="best_plan",
            rationale="the planner selected the best option",
            action_id="a1",
            intent=Intent("apply", {"id": "a1"}),
            requires_approval=True,
            reversible=True,
            score=0.91,
            alternatives=({"id": "a2", "score": 0.4},),
        )


def test_planner_policy_returns_the_one_decision_shape() -> None:
    request = DecisionRequest(
        subject="a task",
        at="2026-11-01T10:00:00+00:00",
        options=(ActionOption(id="a1", verb="act", name="apply"),),
    )
    policy = PlannerPolicy(FakePlanner(), name="fake-planner.v1")
    decision = policy.decide(request, decision_id="DEC-1", trace_id="TRC-1")[0]

    assert decision.decision_id == "DEC-1"
    assert decision.trace_id == "TRC-1"
    assert decision.verb == "act"
    assert decision.action_id == "a1"
    assert decision.requires_approval is True
    assert decision.reversible is True
    assert decision.policy_version == "fake-planner.v1"
    assert decision.intent is not None


def test_to_decision_converts_one_planner_result() -> None:
    request = DecisionRequest(
        subject="a task",
        at="2026-11-01T10:00:00+00:00",
        attributes={"urgency": 0.8},
    )
    planner_result = PlannerResult(
        verb="act",
        confidence=0.9,
        reason_code="best_plan",
        rationale="the best plan",
        action_id="a1",
        attributes={"planner": "utility"},
    )
    decision = to_decision(planner_result, request, policy_version="utility.v1")

    assert decision.verb == "act"
    assert decision.action_id == "a1"
    assert decision.attributes == {"urgency": 0.8, "planner": "utility"}
    assert decision.policy_version == "utility.v1"


def test_to_planner_input_projects_the_request() -> None:
    request = DecisionRequest(
        subject="a task",
        at="2026-11-01T10:00:00+00:00",
        options=(ActionOption(id="a1", verb="act", name="apply"),),
        attributes={"urgency": 0.8},
    )
    problem = to_planner_input(request)

    assert problem.subject == "a task"
    assert problem.attributes["urgency"] == 0.8
    assert problem.options[0].id == "a1"
