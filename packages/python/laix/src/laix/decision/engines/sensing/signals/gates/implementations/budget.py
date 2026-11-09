"""The interruption budget for this cycle is used up."""

from __future__ import annotations

from ......support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def budget(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.signal_interruption_budget is not None and delivered >= context.signal_interruption_budget:
        return GateResult(Verb.WAIT, ReasonCode.BUDGET, False, False)
    return None

__all__ = ["budget"]
