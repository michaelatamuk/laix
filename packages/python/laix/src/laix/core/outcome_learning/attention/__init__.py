"""Attention-specific outcome learning."""

from __future__ import annotations

from .labels import (
    HELPED,
    HURT,
    NEUTRAL,
    REASON_CODES,
    RESULTS,
    UNKNOWN,
    label_for_feedback,
    result_for_reason,
)
from .log import OutcomeLog
from .outcome import AttentionOutcome

__all__ = [
    "HELPED",
    "HURT",
    "NEUTRAL",
    "REASON_CODES",
    "RESULTS",
    "UNKNOWN",
    "AttentionOutcome",
    "OutcomeLog",
    "label_for_feedback",
    "result_for_reason",
]
