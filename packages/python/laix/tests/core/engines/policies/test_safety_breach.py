"""A breached safety boundary escalates when no safe action remains."""

from __future__ import annotations

from laix import ActionOption, Belief, Constraint, DecisionRequest, Layer, Situation


def decision(**attributes):
    return Layer().decide(
        DecisionRequest(
            subject="water near electricity",
            at="2026-11-01T10:00:00+00:00",
            situation=Situation(
                id="leak-1",
                at="2026-11-01T10:00:00+00:00",
                subject="water near electricity",
                beliefs=(Belief(id="leak", proposition="water is leaking", confidence=0.9),),
                constraints=(Constraint(id="risk-limit", kind="risk", value=0.2, hard=True),),
                attributes={"urgency": 0.9, **attributes},
            ),
            options=(
                ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
                ActionOption(id="look", verb="observe", name="look", expected_benefit=0.5),
                ActionOption(id="breaker", verb="act", name="cross wet floor", expected_benefit=1.0, risk=0.9),
                ActionOption(id="manager", verb="escalate", name="call the manager", expected_benefit=0.7),
            ),
        )
    )[0]


def test_a_breached_safety_boundary_escalates() -> None:
    result = decision(safety_breached=True)
    assert result.verb == "escalate"
    assert result.action_id == "manager"
    assert result.score == 0.7
    assert any("risk-limit" in item for item in result.constraints_applied)


def test_without_the_boundary_the_safe_wait_remains() -> None:
    result = decision()
    assert result.verb == "wait"
    assert result.action_id == "wait"
