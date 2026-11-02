"""Attention gates: the fixed order in which a signal can be suppressed.

A gate is a named reason to hold a signal back. The first gate that fires wins;
the order is part of the contract, not an implementation detail.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from .labels import SEVERITY_RANK
from .model.feedback import Feedback

class Gate(StrEnum):
    """A named suppression check. The order below is the decision order."""

    KILL_SWITCH = "kill_switch"
    MUTED = "muted"
    FEEDBACK = "feedback"
    LOW_CONFIDENCE = "low_confidence"
    BELOW_FLOOR = "below_floor"
    ALREADY_SENT = "already_sent"
    QUIET_HOURS = "quiet_hours"
    BUDGET = "budget"
    OVERDUE_ESCALATION = "overdue_escalation"


#: Order in which the gates are applied. The first gate that fires decides.
GATES: tuple[str, ...] = tuple(gate.value for gate in Gate)


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

FEEDBACK_REASONS = {
    "snoozed": ReasonCode.SNOOZED,
    "wrong": ReasonCode.WRONG,
    "assigned": ReasonCode.ASSIGNED,
    "dismissed": ReasonCode.DISMISSED,
}


def rank(severity: str) -> int:
    """Lower is more severe."""
    return SEVERITY_RANK.get(severity, 9)


def snoozed_until_future(until: str | None, now: datetime) -> bool:
    """A snooze with no expiry, or one we cannot read, keeps the signal silent."""
    if not until:
        return True
    try:
        moment = datetime.fromisoformat(until)
    except (TypeError, ValueError):
        return True
    if moment.tzinfo is None and now.tzinfo is not None:
        moment = moment.replace(tzinfo=now.tzinfo)
    return moment > now


def feedback_blocks(feedback: Feedback | None, now: datetime) -> str | None:
    """Return the blocking reason, or None when the signal may proceed."""
    if feedback is None or feedback.state == "accepted":
        return None
    if feedback.state == "snoozed":
        return ReasonCode.SNOOZED if snoozed_until_future(feedback.until, now) else None
    return FEEDBACK_REASONS.get(feedback.state)
