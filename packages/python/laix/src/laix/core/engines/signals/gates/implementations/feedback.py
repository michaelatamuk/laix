"""The user already dismissed, snoozed or rejected this signal."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def feedback(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if blocked is not None:
        return GateResult(Verb.WAIT, blocked, False, False)
    return None

__all__ = ["feedback"]
