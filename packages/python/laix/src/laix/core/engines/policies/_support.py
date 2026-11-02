"""Shared helpers for the packaged policy packs."""

from __future__ import annotations

from typing import Any

from ...decisions import Decision, Intent


def value(request: Any, key: str, default: Any = None) -> Any:
    return (getattr(request, "attributes", {}) or {}).get(key, default)


def number(request: Any, key: str, default: float) -> float:
    try:
        return float(value(request, key, default))
    except (TypeError, ValueError):
        return default


def decision(
    *,
    policy: str,
    verb: str,
    reason_code: str,
    rationale: str,
    confidence: float,
    intent: Intent | None = None,
    score: float | None = None,
    requires_approval: bool = False,
    action_id: str | None = None,
) -> Decision:
    return Decision(
        verb=verb,
        confidence=max(0.0, min(1.0, confidence)),
        reason_code=reason_code,
        rationale=rationale,
        policy_version=policy,
        action_id=action_id,
        requires_approval=requires_approval,
        score=score,
        intent=intent,
    )
