"""Map attention feedback and dismissal reasons to outcome labels.

The labels themselves are generic and live in outcome_learning. This module
knows only the attention-specific vocabulary.
"""

from __future__ import annotations

from ...outcome_learning.record import OUTCOME_LABELS, OutcomeLabel

RESULTS: tuple[str, ...] = OUTCOME_LABELS
HELPED = OutcomeLabel.HELPED
NEUTRAL = OutcomeLabel.NEUTRAL
HURT = OutcomeLabel.HURT
UNKNOWN = OutcomeLabel.UNKNOWN

REASON_CODES: tuple[str, ...] = (
    "false_alarm",
    "design_change",
    "operational",
    "duplicate",
    "no_action",
    "data_error",
)

_HURT_CODES = {"false_alarm", "data_error"}
_NEUTRAL_CODES = {"design_change", "operational", "duplicate", "no_action"}


def result_for_reason(reason_code: str | None) -> OutcomeLabel:
    """Map an app's dismissal reason to a learning label."""
    if not reason_code:
        return UNKNOWN
    code = reason_code.strip().lower()
    if code in _HURT_CODES:
        return HURT
    if code in _NEUTRAL_CODES:
        return NEUTRAL
    return UNKNOWN


def label_for_feedback(state: str, reason_code: str | None = None) -> OutcomeLabel:
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
    "HELPED",
    "HURT",
    "NEUTRAL",
    "REASON_CODES",
    "RESULTS",
    "UNKNOWN",
    "label_for_feedback",
    "result_for_reason",
]
