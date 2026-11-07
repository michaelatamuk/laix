"""Host-supplied confidence and a portable decision basis."""

from __future__ import annotations

from laix import ActionOption, Belief, DecisionRequest, DecisionClient, Situation


def request(**kwargs) -> DecisionRequest:
    return DecisionRequest(
        subject="one task",
        at="2026-11-01T10:00:00+00:00",
        situation=Situation(
            id="task-1",
            at="2026-11-01T10:00:00+00:00",
            subject="one task",
            beliefs=(Belief(id="one", proposition="the task is real", confidence=0.9),),
            attributes={"urgency": 0.9},
        ),
        options=(
            ActionOption(id="a-wait", verb="wait", name="wait", expected_benefit=0.1),
            ActionOption(id="a-act", verb="act", name="act", expected_benefit=0.9),
        ),
        **kwargs,
    )


def test_host_confidence_is_carried_with_its_source() -> None:
    decision = DecisionClient().decide(
        request(confidence=0.86, confidence_source="host-calibrated", calibrated=True)
    )[0]

    assert decision.confidence == 0.86
    assert decision.confidence_source == "host-calibrated"
    assert decision.calibrated is True


def test_decision_basis_is_host_neutral() -> None:
    decision = DecisionClient().decide(request(confidence=0.86, confidence_source="host"))[0]
    basis = decision.basis()

    assert basis[0]["kind"] == "reason"
    assert basis[0]["ref"] == decision.reason_code
    assert basis[0]["note"] == decision.rationale
