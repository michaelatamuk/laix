"""What attention receives."""

from __future__ import annotations

from .signal_context import SignalContext
from .dedupe import dedupe_key
from .signal_feedback import FEEDBACK_STATES, SignalFeedback
from .severity import SEVERITY_RANK, rank
from .signal import Signal

__all__ = [
    "FEEDBACK_STATES",
    "SEVERITY_RANK",
    "SignalContext",
    "SignalFeedback",
    "Signal",
    "dedupe_key",
    "rank",
]
