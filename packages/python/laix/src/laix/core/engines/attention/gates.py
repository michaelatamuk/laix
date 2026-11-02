"""Attention gates: the fixed order in which a signal can be suppressed.

A gate is a named reason to hold a signal back. The first gate that fires wins;
the order is part of the contract, not an implementation detail.
"""

from __future__ import annotations

from datetime import datetime

from .labels import SEVERITY_RANK
from .model.feedback import Feedback

#: Order in which the gates are applied. The first gate that fires decides.
GATES: tuple[str, ...] = (
    "kill_switch",
    "muted",
    "feedback",
    "low_confidence",
    "below_floor",
    "already_sent",
    "quiet_hours",
    "budget",
    "overdue_escalation",
)

#: Every reason a decision can carry. A vector file may not invent one.
REASONS: tuple[str, ...] = (
    "worth_surfacing",
    "kill_switch",
    "muted",
    "snoozed",
    "wrong",
    "assigned",
    "dismissed",
    "low_confidence",
    "below_floor",
    "already_sent",
    "quiet_hours",
    "budget",
    "overdue_escalation",
    "act",
    "ask_approval",
)

FEEDBACK_REASONS = {"snoozed": "snoozed", "wrong": "wrong", "assigned": "assigned", "dismissed": "dismissed"}


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
        return "snoozed" if snoozed_until_future(feedback.until, now) else None
    return FEEDBACK_REASONS.get(feedback.state)
