"""The interruption budget for this cycle is used up."""

from __future__ import annotations

from .....support.verbs import Verb
from ...model.context import Context
from ...model.signal import Signal
from ..gate_result import GateResult
from ..reasons import ReasonCode


def budget(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.interruption_budget is not None and delivered >= context.interruption_budget:
        return GateResult(Verb.WAIT, ReasonCode.BUDGET, False, False)
    return None

__all__ = ["budget"]
