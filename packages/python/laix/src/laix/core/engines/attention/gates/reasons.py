"""The reason codes an attention decision may carry."""

from __future__ import annotations

from enum import StrEnum


class ReasonCode(StrEnum):
    """Every reason an attention decision can carry."""

    WORTH_SURFACING = "worth_surfacing"
    KILL_SWITCH = "kill_switch"
    MUTED = "muted"
    SNOOZED = "snoozed"
    WRONG = "wrong"
    ASSIGNED = "assigned"
    DISMISSED = "dismissed"
    LOW_CONFIDENCE = "low_confidence"
    BELOW_FLOOR = "below_floor"
    ALREADY_SENT = "already_sent"
    QUIET_HOURS = "quiet_hours"
    BUDGET = "budget"
    OVERDUE_ESCALATION = "overdue_escalation"
    ACT = "act"
    ASK_APPROVAL = "ask_approval"


#: Every reason a decision can carry. A vector file may not invent one.
REASONS: tuple[str, ...] = tuple(reason.value for reason in ReasonCode)

#: A feedback state that suppresses a signal, mapped to its reason.
FEEDBACK_REASONS = {
    "snoozed": ReasonCode.SNOOZED,
    "wrong": ReasonCode.WRONG,
    "assigned": ReasonCode.ASSIGNED,
    "dismissed": ReasonCode.DISMISSED,
}

__all__ = ["FEEDBACK_REASONS", "REASONS", "ReasonCode"]
