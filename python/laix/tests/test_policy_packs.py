"""Reference policy packs for the remaining LAIX decision classes."""

from __future__ import annotations

from laix import (
    ActivePerceptionPolicy,
    AllocationPolicy,
    DecisionRequest,
    Layer,
    NegotiationPolicy,
    PreferenceElicitationPolicy,
    ReplanningPolicy,
    SafetyConstrainedPolicy,
)


def request(**attributes):
    return DecisionRequest(subject="case-1", at="2026-11-01T10:00:00+00:00", attributes=attributes)


def decide(policy, **attributes):
    return Layer(policy=policy).decide(request(**attributes))[0]


def test_active_perception_observes_when_uncertainty_is_high() -> None:
    decision = decide(
        ActivePerceptionPolicy(),
        uncertainty=0.8,
        observations=[{"id": "look-1", "information_gain": 0.7, "cost": 0.1}],
    )
    assert decision.verb == "observe"
    assert decision.intent is not None
    assert decision.intent.capability == "observe"


def test_active_perception_waits_at_low_uncertainty() -> None:
    decision = decide(ActivePerceptionPolicy(), uncertainty=0.1, observations=[])
    assert decision.verb == "wait"
    assert decision.reason_code == "uncertainty_low"


def test_safety_policy_acts_only_inside_the_risk_limit() -> None:
    decision = decide(
        SafetyConstrainedPolicy(),
        risk_limit=0.2,
        options=[
            {"id": "safe", "benefit": 0.9, "risk": 0.1},
            {"id": "risky", "benefit": 1.0, "risk": 0.9},
        ],
    )
    assert decision.verb == "act"
    assert decision.action_id == "safe"


def test_safety_policy_waits_when_nothing_is_safe() -> None:
    decision = decide(
        SafetyConstrainedPolicy(),
        risk_limit=0.1,
        options=[{"id": "risky", "benefit": 1.0, "risk": 0.9}],
    )
    assert decision.verb == "wait"
    assert decision.reason_code == "no_safe_option"


def test_replanning_picks_a_feasible_plan() -> None:
    decision = decide(
        ReplanningPolicy(),
        plans=[
            {"id": "slow", "success_probability": 0.95, "cost": 10, "deadline_risk": 0.1},
            {"id": "fast", "success_probability": 0.8, "cost": 1, "deadline_risk": 0.1},
        ],
        min_success=0.7,
        max_cost=5,
    )
    assert decision.verb == "act"
    assert decision.action_id == "fast"


def test_allocation_funds_requests_inside_the_budget() -> None:
    decision = decide(
        AllocationPolicy(),
        budget=10,
        requests=[
            {"id": "a", "value": 6, "cost": 4},
            {"id": "b", "value": 5, "cost": 6},
            {"id": "c", "value": 9, "cost": 20},
        ],
    )
    assert decision.verb == "act"
    assert decision.intent is not None
    assert decision.intent.args["ids"] == ["a", "b"]


def test_negotiation_counters_accepts_and_escalates() -> None:
    counter = decide(NegotiationPolicy(), offer=5, reservation=10, target=20, round=1)
    assert counter.verb == "act"
    assert counter.intent is not None
    assert counter.intent.capability == "counter_offer"

    accepted = decide(NegotiationPolicy(), offer=12, reservation=10, target=20, round=1)
    assert accepted.verb == "act"
    assert accepted.intent is not None
    assert accepted.intent.capability == "accept_offer"

    escalated = decide(NegotiationPolicy(), offer=5, reservation=10, target=20, round=5)
    assert escalated.verb == "escalate"


def test_preference_elicitation_asks_the_best_question() -> None:
    decision = decide(
        PreferenceElicitationPolicy(),
        uncertainty=0.8,
        questions=[
            {"id": "q1", "information_gain": 0.2, "cost": 1},
            {"id": "q2", "information_gain": 0.8, "cost": 1},
        ],
    )
    assert decision.verb == "ask"
    assert decision.intent is not None
    assert decision.intent.args["id"] == "q2"
