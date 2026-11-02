"""A signal kind the user muted."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from .reasons import ReasonCode


def muted(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if signal.kind in context.muted_kinds:
        return GateResult(Verb.WAIT, ReasonCode.MUTED, False, False)
    return None

__all__ = ["muted"]
