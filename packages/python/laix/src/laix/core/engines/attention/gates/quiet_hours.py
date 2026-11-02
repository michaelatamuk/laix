"""It is quiet time, unless the signal is critical."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from ..timing import is_quiet
from .reasons import ReasonCode


def quiet_hours(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if is_quiet(context.now, context.quiet_hours) and signal.severity != "critical":
        return GateResult(Verb.WAIT, ReasonCode.QUIET_HOURS, True, False)
    return None

__all__ = ["quiet_hours"]
