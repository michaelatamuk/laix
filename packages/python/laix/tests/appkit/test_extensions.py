"""The generic extensions: policy plugins, proposals, delivery and parity."""

from __future__ import annotations

import pytest

from laix import (
    Case,
    DecisionRequest,
    DeliveryReceipt,
    DecisionClient,
    Decision,
    NullDelivery,
    DecisionPolicyError,
    Proposal,
    apply_proposal,
    approve_proposal,
    compare_decisions,
    reject_proposal,
    undo_proposal,
)


class FixedPolicy:
    name = "fixed"
    version = "1.0"

    def decide(self, request):
        return [
            Decision(
                verb="guide",
                confidence=0.8,
                reason_code="worth_surfacing",
                rationale="test policy",
                score=10.0,
            )
        ]


def request() -> DecisionRequest:
    return DecisionRequest(subject="one decision", at="2026-11-01T10:00:00+00:00")


def test_a_policy_plugin_drives_the_decision_client() -> None:
    layer = DecisionClient(policy=FixedPolicy())
    decisions = layer.decide(request())
    assert decisions[0].verb == "guide"
    assert decisions[0].reason_code == "worth_surfacing"
    assert layer.status()["policy"] == "fixed"
    assert layer.status()["policyVersion"] == "1.0"
    assert layer.status()["decisions"] == 1


def test_a_policy_can_be_registered_and_selected() -> None:
    layer = DecisionClient()
    layer.register_policy("fixed", FixedPolicy())
    assert layer.policies() == ("fixed",)
    layer.use_policy("fixed")
    assert layer.decide(request())[0].verb == "guide"
    with pytest.raises(DecisionPolicyError):
        layer.use_policy("missing")


def test_explain_returns_the_decision_record_fields() -> None:
    layer = DecisionClient(policy=FixedPolicy())
    decision = layer.decide(request())[0]
    explained = layer.explain(decision)
    assert explained["verb"] == "guide"
    assert explained["reasonCode"] == "worth_surfacing"
    assert explained["evidence"] == []
    assert explained["traceId"].startswith("TRC-")


def test_proposal_lifecycle() -> None:
    proposal = Proposal(id="p-1", title="One change", summary="Apply the change")
    assert proposal.status == "pending"
    approved = approve_proposal(proposal, by="owner")
    assert approved.status == "approved"
    applied = apply_proposal(approved)
    assert applied.status == "applied"
    undone = undo_proposal(applied)
    assert undone.status == "undone"


def test_proposal_rejection_and_invalid_transition() -> None:
    rejected = reject_proposal(Proposal(id="p-1", title="One change", summary="Apply"), by="owner")
    assert rejected.status == "rejected"
    with pytest.raises(ValueError):
        apply_proposal(rejected)


def test_delivery_port_returns_a_receipt() -> None:
    port = NullDelivery()
    receipt = port.deliver(Decision(verb="guide", confidence=0.8, reason_code="x", rationale="x"), "hello")
    assert isinstance(receipt, DeliveryReceipt)
    assert receipt.status == "skipped"
    assert len(port.receipts) == 1


def test_parity_harness_compares_and_reports() -> None:
    cases = (
        Case(id="a", request=None, expected=({"verb": "guide", "reason_code": "x"},)),
        Case(id="b", request=None, expected=({"verb": "wait", "reason_code": "y"},)),
    )

    def decide(_request):
        return [{"verb": "guide", "reason_code": "x"}]

    report = compare_decisions(cases, decide)
    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1
    assert report.to_dict()["agreementRate"] == 0.5
