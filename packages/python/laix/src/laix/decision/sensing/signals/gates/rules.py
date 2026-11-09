"""The gate order. This is the attention behaviour."""

from __future__ import annotations

from .implementations.act import act
from .implementations.already_sent import already_sent
from .implementations.below_floor import below_floor
from .implementations.budget import budget
from .implementations.feedback import feedback
from .gate import Gate
from .implementations.kill_switch import kill_switch
from .implementations.low_confidence import low_confidence
from .implementations.muted import muted
from .implementations.overdue_escalation import overdue_escalation
from .implementations.quiet_hours import quiet_hours

#: The first gate that fires decides. Change this tuple to change behaviour.
GATE_RULES = (
    (Gate.KILL_SWITCH, kill_switch),
    (Gate.MUTED, muted),
    (Gate.FEEDBACK, feedback),
    (Gate.LOW_CONFIDENCE, low_confidence),
    (Gate.BELOW_FLOOR, below_floor),
    (Gate.ALREADY_SENT, already_sent),
    (Gate.QUIET_HOURS, quiet_hours),
    (Gate.BUDGET, budget),
    (Gate.OVERDUE_ESCALATION, overdue_escalation),
    (Gate.ACT, act),
)

GATES: tuple[str, ...] = tuple(gate.value for gate, _ in GATE_RULES)

__all__ = ["GATES", "GATE_RULES"]
