"""Core-only entry point: choose an engine and return decisions.

This module never imports the app kit. It is the small surface a host can use
when it wants decisions without runtime traces, execution or records.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any

from .decisions import Decision, DecisionRequest, coerce, from_attention
from .engines.attention import decide_attention
from .engines.policies import ActionPolicy, ActionPolicyRequest
from .support.ids import new_id


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


def decide(
    request: DecisionRequest,
    policy: Any = None,
    *,
    id_factory: Callable[[str], str] | None = None,
) -> list[Decision]:
    """Return decisions without the app kit.

    Pass ``policy=`` to use a specific policy. Otherwise the request shape
    selects the built-in action policy or the attention engine. Every decision
    gets a ``decision_id``; a ``trace_id`` is generated when the engine did not
    provide one.
    """
    make_id = id_factory or new_id
    route = select(request, policy)
    if route == "policy":
        return [
            annotate_confidence(_identify(coerce(item), make_id), request)
            for item in policy.decide(request)
        ]

    if route == "action":
        if request.situation is None:
            raise ValueError("action selection needs a situation")
        action_request = ActionPolicyRequest(
            situation=request.situation,
            options=request.options,
            attributes=attributes_for(request),
        )
        return [
            annotate_confidence(
                _identify(ActionPolicy().decide(action_request), make_id), request
            )
        ]

    if request.context is None:
        raise ValueError("attention allocation needs a context with now")
    return [
        annotate_confidence(_identify(from_attention(item), make_id), request)
        for item in decide_attention(request.signals, request.context)
    ]


def _identify(decision: Decision, make_id: Callable[[str], str]) -> Decision:
    changes: dict[str, str] = {}
    if not decision.decision_id:
        changes["decision_id"] = make_id("DEC")
    if not decision.trace_id:
        changes["trace_id"] = make_id("TRC")
    return replace(decision, **changes) if changes else decision


__all__ = [
    "annotate_confidence",
    "attributes_for",
    "decide",
    "select",
]
