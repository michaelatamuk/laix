"""What attention receives."""

from __future__ import annotations

from .context import Context
from .dedupe import dedupe_key
from .feedback import FEEDBACK_STATES, Feedback
from .severity import SEVERITY_RANK, rank
from .signal import Signal

__all__ = [
    "FEEDBACK_STATES",
    "SEVERITY_RANK",
    "Context",
    "Feedback",
    "Signal",
    "dedupe_key",
    "rank",
]
