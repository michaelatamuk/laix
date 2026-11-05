"""The name of each attention gate."""

from __future__ import annotations

from enum import StrEnum


class Gate(StrEnum):
    """A named check. The order lives in ``rules.py``."""

    KILL_SWITCH = "kill_switch"
    MUTED = "muted"
    FEEDBACK = "feedback"
    LOW_CONFIDENCE = "low_confidence"
    BELOW_FLOOR = "below_floor"
    ALREADY_SENT = "already_sent"
    QUIET_HOURS = "quiet_hours"
    BUDGET = "budget"
    OVERDUE_ESCALATION = "overdue_escalation"
    ACT = "act"


__all__ = ["Gate"]
