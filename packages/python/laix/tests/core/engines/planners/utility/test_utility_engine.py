"""The expected-utility engine and its hard limits."""

from __future__ import annotations

from laix import (
    ActionOption,
    ActionPolicy,
    ActionPolicyRequest,
    Constraint,
    DecisionProblem,
    Situation,
    UtilityEngine,
    UtilityModel,
    UtilityWeights,
)


def _problem(*options: ActionOption, **attributes: object) -> DecisionProblem:
    return DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        options=options,
        attributes=dict(attributes),
    )


def test_utility_engine_chooses_the_highest_expected_utility() -> None:
    engine = UtilityEngine()
    plan = engine.solve(
        _problem(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        )
    )

    assert plan.verb == "act"
    assert plan.action_id == "bold"
    assert plan.score == 0.75


def test_risk_aversion_changes_the_choice() -> None:
    options = (
        ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
        ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.8, risk=0.6),
    )
    neutral = UtilityEngine().solve(_problem(*options))
    averse = UtilityEngine(UtilityModel(risk_attitude="averse")).solve(_problem(*options))

    assert neutral.action_id == "bold"
    assert averse.action_id == "safe"


def test_hard_limit_rejects_an_option() -> None:
    plan = UtilityEngine(UtilityModel(max_risk=0.4)).solve(
        _problem(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        )
    )

    assert plan.action_id == "safe"
    assert plan.alternatives[0]["action_id"] == "bold"
    assert plan.alternatives[0]["rejected_because"] == "outside the hard limits"


def test_no_options_waits() -> None:
    plan = UtilityEngine().solve(_problem())

    assert plan.verb == "wait"
    assert plan.reason_code == "no_options"


def test_weights_must_not_be_negative() -> None:
    try:
        UtilityWeights(cost=-1)
    except ValueError as exc:
        assert "must not be negative" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_utility_engine_agrees_with_the_action_policy() -> None:
    options = (
        ActionOption(id="a1", verb="act", name="close", expected_benefit=0.9, risk=0.1),
        ActionOption(id="a2", verb="act", name="wait", expected_benefit=0.6, risk=0.1),
    )
    situation = Situation(
        id="sit-1",
        at="2026-11-01T10:00:00+00:00",
        subject="leak",
        attributes={"confidence": 0.95, "urgency": 0.95},
    )
    action = ActionPolicy().decide(
        ActionPolicyRequest(situation=situation, options=options)
    )
    utility = UtilityEngine().solve(_problem(*options))

    assert action.action_id == utility.action_id == "a1"


def test_hard_situation_constraint_rejects_an_option() -> None:
    situation = Situation(
        id="sit-1",
        at="2026-11-01T10:00:00+00:00",
        subject="leak",
        constraints=(Constraint(id="risk-limit", kind="risk", value=0.2),),
    )
    problem = DecisionProblem(
        subject="choose",
        at="2026-11-01T10:00:00+00:00",
        situation=situation,
        options=(
            ActionOption(id="safe", verb="act", name="safe", expected_benefit=0.6, risk=0.1),
            ActionOption(id="bold", verb="act", name="bold", expected_benefit=0.9, risk=0.6),
        ),
    )
    plan = UtilityEngine().solve(problem)

    assert plan.action_id == "safe"
    assert plan.alternatives[0]["action_id"] == "bold"
    assert plan.alternatives[0]["rejected_because"] == "blocked by risk:risk-limit"


def test_safety_constraint_blocks_every_option() -> None:
    situation = Situation(
        id="sit-1",
        at="2026-11-01T10:00:00+00:00",
        subject="leak",
        constraints=(Constraint(id="stop", kind="safety", value=True),),
    )
    plan = UtilityEngine().solve(
        DecisionProblem(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            situation=situation,
            options=(ActionOption(id="a1", verb="act", name="go"),),
        )
    )

    assert plan.verb == "wait"
    assert plan.reason_code == "no_feasible_option"


def test_approval_constraint_sets_the_flag() -> None:
    situation = Situation(
        id="sit-1",
        at="2026-11-01T10:00:00+00:00",
        subject="payment",
        constraints=(Constraint(id="human", kind="approval", value=True),),
    )
    plan = UtilityEngine().solve(
        DecisionProblem(
            subject="choose",
            at="2026-11-01T10:00:00+00:00",
            situation=situation,
            options=(ActionOption(id="pay", verb="act", name="pay"),),
        )
    )

    assert plan.requires_approval is True
