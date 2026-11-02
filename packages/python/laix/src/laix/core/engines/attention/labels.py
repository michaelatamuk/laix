"""Outcome labels and the mapping from reasons or feedback to a label.

This is the smallest honest version. It maps a reason code to a result; the
recording contract stays the same no matter which learner consumes it.
"""

from __future__ import annotations

SEVERITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
RESULTS: tuple[str, ...] = ("helped", "neutral", "hurt", "unknown")
FEEDBACK_STATES: tuple[str, ...] = ("accepted", "dismissed", "snoozed", "wrong", "assigned")
REASON_CODES: tuple[str, ...] = (
    "false_alarm",
    "design_change",
    "operational",
    "duplicate",
    "no_action",
    "data_error",
)

HELPED = "helped"
NEUTRAL = "neutral"
HURT = "hurt"
UNKNOWN = "unknown"

_HURT_CODES = {"false_alarm", "data_error"}
_NEUTRAL_CODES = {"design_change", "operational", "duplicate", "no_action"}


def result_for_reason(reason_code: str | None) -> str:
    """Map an app's dismissal reason to a learning label."""
    if not reason_code:
        return UNKNOWN
    code = reason_code.strip().lower()
    if code in _HURT_CODES:
        return HURT
    if code in _NEUTRAL_CODES:
        return NEUTRAL
    return UNKNOWN


def label_for_feedback(state: str, reason_code: str | None = None) -> str:
    """A UI feedback state (accepted, dismissed, snoozed, wrong) to a result."""
    state = (state or "").strip().lower()
    if state in {"accepted", "confirmed", "signed"}:
        return HELPED
    if state in {"wrong", "false_alarm"}:
        return HURT
    if state in {"dismissed", "snoozed", "assigned"}:
        return result_for_reason(reason_code)
    return UNKNOWN


__all__ = [
    "FEEDBACK_STATES",
    "HELPED",
    "HURT",
    "NEUTRAL",
    "REASON_CODES",
    "RESULTS",
    "SEVERITY_RANK",
    "UNKNOWN",
    "label_for_feedback",
    "result_for_reason",
]
