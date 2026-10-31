"""Reference policy packs for the remaining LAIX decision classes."""

from __future__ import annotations

from laix import (
    ActivePerceptionPolicy,
    AllocationPolicy,
    DecisionRequest,
    EscalationPolicy,
    Layer,
    NegotiationPolicy,
    PreferenceElicitationPolicy,
    ReplanningPolicy,
    SafetyConstrainedPolicy,
    VerificationPolicy,
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


def test_verification_picks_the_best_check() -> None:
    decision = decide(
        VerificationPolicy(),
        confidence=0.5,
        required_confidence=0.8,
        checks=[
            {"id": "manual", "confidence_gain": 0.2, "cost": 1},
            {"id": "api", "confidence_gain": 0.8, "cost": 1},
        ],
    )
    assert decision.verb == "verify"
    assert decision.action_id == "api"
    assert decision.intent is not None
    assert decision.intent.capability == "verify"


def test_verification_escalates_without_a_path() -> None:
    decision = decide(VerificationPolicy(), confidence=0.3, required_confidence=0.8, checks=[])
    assert decision.verb == "escalate"
    assert decision.reason_code == "no_verification_path"
    assert decision.escalation is not None
    assert decision.escalation.target == "human"


def test_verification_is_not_needed_when_confident() -> None:
    decision = decide(
        VerificationPolicy(),
        confidence=0.95,
        required_confidence=0.8,
        verification_due=False,
        checks=[],
    )
    assert decision.verb == "wait"
    assert decision.reason_code == "verification_not_needed"


def test_escalation_hands_over_to_a_target() -> None:
    decision = decide(EscalationPolicy(), severity=0.9, severity_threshold=0.8, target="manager")
    assert decision.verb == "escalate"
    assert decision.action_id == "manager"
    assert decision.escalation is not None
    assert decision.escalation.target == "manager"


def test_escalation_waits_within_limits() -> None:
    decision = decide(EscalationPolicy(), severity=0.2, severity_threshold=0.8, confidence=0.9)
    assert decision.verb == "wait"
    assert decision.reason_code == "within_limits"


def test_escalation_asks_for_a_target_when_missing() -> None:
    decision = decide(EscalationPolicy(), severity=0.9, severity_threshold=0.8)
    assert decision.verb == "ask"
    assert decision.reason_code == "target_required"
