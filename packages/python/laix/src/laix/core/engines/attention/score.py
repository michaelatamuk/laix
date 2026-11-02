"""Attention scoring: the inspectable breakdown kept with every decision.

The score is recorded and explained, but it does not choose the verb in v1.
Gates do that. A learned scorer can replace this later without changing the
decision shape.
"""

from __future__ import annotations

from datetime import datetime

from ...decisions import ScoreBreakdown
from .model.context import Context
from .model.signal import Signal
from .timing import hours_until
from ...support.verbs import Verb

SEVERITY_POINTS = {"critical": 60.0, "high": 45.0, "medium": 30.0, "low": 15.0, "info": 5.0}
#: How much an hour of silence costs, relative to severity.
WAIT_FACTOR = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.5, "info": 0.25}


def due_points(now: datetime, due: str | None) -> float:
    hours = hours_until(now, due)
    if hours is None:
        return 0.0
    if hours < 0:
        return 30.0
    if hours <= 24:
        return 20.0
    if hours <= 72:
        return 12.0
    if hours <= 168:
        return 6.0
    return 0.0


def score(signal: Signal, context: Context) -> ScoreBreakdown:
    severity = SEVERITY_POINTS.get(signal.severity, 5.0)
    due = due_points(context.now, signal.due)
    confidence = max(0.0, min(1.0, signal.confidence)) * 20.0
    interruption = -max(0.0, min(1.0, signal.interruption_cost)) * 20.0
    learned = float(context.learned.get(signal.kind, 0.0))
    total = severity + due + confidence + interruption + learned
    return ScoreBreakdown(severity, due, confidence, interruption, learned, total)


def cost_of_waiting(signal: Signal, context: Context) -> float:
    """Points at stake if the decision is silence. Zero without a deadline."""
    factor = WAIT_FACTOR.get(signal.severity, 0.25)
    return round(due_points(context.now, signal.due) * factor, 2)


def undo_hint(verb: str, reversible: bool) -> str | None:
    if verb in {Verb.GUIDE, Verb.ASK}:
        return "withdraw"
    if verb == Verb.ACT:
        return "cancel" if reversible else None
    return None
