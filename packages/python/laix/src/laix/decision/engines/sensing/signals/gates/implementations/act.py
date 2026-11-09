"""The app opted in and the action is reversible."""

from __future__ import annotations

from ......support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def act(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.allow_act and signal.intent is not None and signal.reversible:
        return GateResult(Verb.ACT, ReasonCode.ACT, True, True)
    return None

__all__ = ["act"]
