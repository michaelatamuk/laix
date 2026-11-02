"""The gate order. This is the attention behaviour."""

from __future__ import annotations

from .act import act
from .already_sent import already_sent
from .below_floor import below_floor
from .budget import budget
from .feedback import feedback
from .gate import Gate
from .kill_switch import kill_switch
from .low_confidence import low_confidence
from .muted import muted
from .overdue_escalation import overdue_escalation
from .quiet_hours import quiet_hours

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
