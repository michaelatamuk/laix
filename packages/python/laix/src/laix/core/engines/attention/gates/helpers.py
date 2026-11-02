"""Shared helpers used by more than one gate."""

from __future__ import annotations

from datetime import datetime

from ..model.severity import SEVERITY_RANK
from ..model.feedback import Feedback
from ..model.signal import Signal
from .reasons import FEEDBACK_REASONS, ReasonCode


def rank(severity: str) -> int:
    """Lower is more severe."""
    return SEVERITY_RANK.get(severity, 9)


def dedupe_key(signal: Signal, now: datetime) -> str:
    """One interruption per signal per day, by default."""
    return f"{signal.id}:{now.date().isoformat()}"


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


def feedback_blocks(feedback: Feedback | None, now: datetime) -> ReasonCode | None:
    """Return the blocking reason, or None when the signal may proceed."""
    if feedback is None or feedback.state == "accepted":
        return None
    if feedback.state == "snoozed":
        return ReasonCode.SNOOZED if snoozed_until_future(feedback.until, now) else None
    return FEEDBACK_REASONS.get(feedback.state)


__all__ = ["dedupe_key", "feedback_blocks", "rank", "snoozed_until_future"]
