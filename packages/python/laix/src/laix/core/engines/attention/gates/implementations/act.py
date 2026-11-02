"""The app opted in and the action is reversible."""

from __future__ import annotations

from .....support.verbs import Verb
from ...model.context import Context
from ...model.signal import Signal
from ..gate_result import GateResult
from ..reasons import ReasonCode


def act(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.allow_act and signal.intent is not None and signal.reversible:
        return GateResult(Verb.ACT, ReasonCode.ACT, True, True)
    return None

__all__ = ["act"]
