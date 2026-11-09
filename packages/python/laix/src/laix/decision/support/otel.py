"""OpenTelemetry attribute names for one decision.

The package does not depend on an OpenTelemetry SDK. The host attaches these
values to its own span, log or metric. Names are stable; values are primitives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..domain.decisions import Decision


def decision_attributes(decision: "Decision") -> dict[str, Any]:
    """Map one decision onto stable OpenTelemetry attribute names."""
    attributes: dict[str, Any] = {
        "laix.verb": decision.verb,
        "laix.reason_code": decision.reason_code,
        "laix.confidence": decision.confidence,
        "laix.approval.required": decision.requires_approval,
        "laix.reversible": decision.reversible,
        "laix.status": decision.status,
        "laix.target": decision.target,
        "laix.calibrated": decision.calibrated,
        "laix.schema.version": decision.schema_version,
    }
    optional: dict[str, Any] = {
        "laix.decision.id": decision.decision_id,
        "laix.trace.id": decision.trace_id,
        "laix.situation.id": decision.situation_id,
        "laix.action.id": decision.action_id,
        "laix.policy.version": decision.policy_version,
        "laix.confidence.source": decision.confidence_source,
        "laix.stream.id": decision.stream_id,
        "laix.supersedes": decision.supersedes,
        "laix.event.time": decision.event_time,
    }
    for name, value in optional.items():
        if value not in (None, ""):
            attributes[name] = value
    if decision.score is not None:
        attributes["laix.score"] = decision.score
    if decision.revision:
        attributes["laix.revision"] = decision.revision
    return attributes


__all__ = ["decision_attributes"]
