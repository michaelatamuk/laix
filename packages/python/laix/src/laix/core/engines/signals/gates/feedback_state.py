"""SignalFeedback suppression: has the user already rejected this signal?"""

from __future__ import annotations

from datetime import datetime

from ..input.signal_feedback import SignalFeedback
from .reason import FEEDBACK_REASONS, ReasonCode


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


def feedback_blocks(feedback: SignalFeedback | None, now: datetime) -> ReasonCode | None:
    """Return the blocking reason, or None when the signal may proceed."""
    if feedback is None or feedback.state == "accepted":
        return None
    if feedback.state == "snoozed":
        return ReasonCode.SNOOZED if snoozed_until_future(feedback.until, now) else None
    return FEEDBACK_REASONS.get(feedback.state)


__all__ = ["feedback_blocks", "snoozed_until_future"]
