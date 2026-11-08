"""A signal kind the user muted."""

from __future__ import annotations

from ......support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def muted(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if signal.kind in context.muted_kinds:
        return GateResult(Verb.WAIT, ReasonCode.MUTED, False, False)
    return None

__all__ = ["muted"]
