"""Core-only entry point: choose an engine and return decisions.

This module never imports the app kit. It is the small surface a host can use
when it wants decisions without runtime traces, execution or records.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .decisions import Decision, DecisionRequest, coerce, from_attention
from .engines.attention import decide_attention
from .engines.policies import ActionPolicy, ActionPolicyRequest


def select(request: DecisionRequest, policy: Any = None) -> str:
    """Name the handler for this request: policy, action or attention."""
    if policy is not None:
        return "policy"
    if request.situation is not None or request.options:
        return "action"
    if request.signals or request.context is not None:
        return "attention"
    raise ValueError("request has neither a situation/options nor signals/context")


def attributes_for(request: DecisionRequest) -> dict[str, Any]:
    """Merge the request's confidence fields into policy attributes."""
    attributes = dict(request.attributes)
    if request.confidence is not None:
        attributes.setdefault("confidence", request.confidence)
    if request.confidence_source:
        attributes.setdefault("confidence_source", request.confidence_source)
    if request.calibrated:
        attributes.setdefault("calibrated", True)
    return attributes


def annotate_confidence(decision: Decision, request: DecisionRequest) -> Decision:
    """Carry the request's confidence provenance onto a decision."""
    source = request.confidence_source or decision.confidence_source
    calibrated = request.calibrated or decision.calibrated
    if source == decision.confidence_source and calibrated == decision.calibrated:
        return decision
    return replace(decision, confidence_source=source, calibrated=calibrated)


def decide(request: DecisionRequest, policy: Any = None) -> list[Decision]:
    """Return decisions without the app kit.

    Pass ``policy=`` to use a specific policy. Otherwise the request shape
    selects the built-in action policy or the attention engine.
    """
    route = select(request, policy)
    if route == "policy":
        return [annotate_confidence(coerce(item), request) for item in policy.decide(request)]

    if route == "action":
        if request.situation is None:
            raise ValueError("action selection needs a situation")
        action_request = ActionPolicyRequest(
            situation=request.situation,
            options=request.options,
            attributes=attributes_for(request),
        )
        return [annotate_confidence(ActionPolicy().decide(action_request), request)]

    if request.context is None:
        raise ValueError("attention allocation needs a context with now")
    return [
        annotate_confidence(from_attention(item), request)
        for item in decide_attention(request.signals, request.context)
    ]


__all__ = [
    "annotate_confidence",
    "attributes_for",
    "decide",
    "select",
]
