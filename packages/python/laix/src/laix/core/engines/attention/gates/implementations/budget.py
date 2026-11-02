"""The interruption budget for this cycle is used up."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.context import Context
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def budget(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.interruption_budget is not None and delivered >= context.interruption_budget:
        return GateResult(Verb.WAIT, ReasonCode.BUDGET, False, False)
    return None

__all__ = ["budget"]
