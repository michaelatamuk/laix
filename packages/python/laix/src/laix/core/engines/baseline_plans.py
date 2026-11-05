"""Shared plan helpers for the naive benchmark baselines."""

from __future__ import annotations

from ..decisions import ActionOption
from .plan import Plan


def baseline_plan(option: ActionOption, reason_code: str, rationale: str) -> Plan:
    return Plan(
        verb=option.verb,
        confidence=1.0,
        reason_code=reason_code,
        rationale=rationale,
        action_id=option.id,
        requires_approval=option.requires_approval or option.destructive,
        reversible=option.reversible,
        score=option.utility,
    )


def baseline_wait(reason_code: str, rationale: str) -> Plan:
    return Plan(
        verb="wait",
        confidence=1.0,
        reason_code=reason_code,
        rationale=rationale,
        score=0.0,
    )


__all__ = ["baseline_plan", "baseline_wait"]
