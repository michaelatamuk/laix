"""Attention gates, one file per gate.

Read ``rules.py`` for the order, then the file named after the gate.
"""

from __future__ import annotations

from .implementations.act import act
from .implementations.already_sent import already_sent
from .implementations.below_floor import below_floor
from .implementations.budget import budget
from .implementations.feedback import feedback
from .gate import Gate
from .result import GateResult
from ..input.dedupe import dedupe_key
from ..input.severity import rank
from .feedback_state import feedback_blocks, snoozed_until_future
from .implementations.kill_switch import kill_switch
from .implementations.low_confidence import low_confidence
from .implementations.muted import muted
from .implementations.overdue_escalation import overdue_escalation
from .implementations.quiet_hours import quiet_hours
from .reason import FEEDBACK_REASONS, REASONS, ReasonCode
from .rules import GATES, GATE_RULES

__all__ = [
    "FEEDBACK_REASONS",
    "GATES",
    "GATE_RULES",
    "Gate",
    "GateResult",
    "REASONS",
    "ReasonCode",
    "act",
    "already_sent",
    "below_floor",
    "budget",
    "dedupe_key",
    "feedback",
    "feedback_blocks",
    "kill_switch",
    "low_confidence",
    "muted",
    "overdue_escalation",
    "quiet_hours",
    "rank",
    "snoozed_until_future",
]
