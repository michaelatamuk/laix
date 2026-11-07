"""It is quiet time, unless the signal is critical."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ...timing import is_quiet
from ..reason import ReasonCode


def quiet_hours(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if is_quiet(context.now, context.quiet_hours) and signal.severity != "critical":
        return GateResult(Verb.WAIT, ReasonCode.QUIET_HOURS, True, False)
    return None

__all__ = ["quiet_hours"]
