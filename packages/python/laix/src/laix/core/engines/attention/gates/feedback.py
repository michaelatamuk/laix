"""The user already dismissed, snoozed or rejected this signal."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from .reasons import ReasonCode


def feedback(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if blocked is not None:
        return GateResult(Verb.WAIT, blocked, False, False)
    return None

__all__ = ["feedback"]
