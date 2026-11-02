"""LAIX attention — a small, domain-free decision layer for the right moment.

Given a candidate intervention, the current context and the user's limits,
should the product **wait, observe, guide, ask, act, verify or escalate**?

A generic policy inside LAIX. No framework, no agent runtime, no app types, no
network, no database, no clock of its own.
"""

from __future__ import annotations

from ...decisions import ScoreBreakdown, Intent
from ...support.verbs import VERBS
from .model.decision import AttentionDecision
from .ports.clock import Clock
from .model.context import Context
from .model.feedback import FEEDBACK_STATES, Feedback
from .model.severity import SEVERITY_RANK
from .ports.null_sink import NullSink
from .decide import decide_attention, decide_one, dedupe_key, rollup, trace_id
from .gates import GATES, GATE_RULES, REASONS, Gate, ReasonCode, feedback_blocks, rank
from .score import SEVERITY_POINTS, WAIT_FACTOR, cost_of_waiting, score
from .undo import undo_hint
from .ports.recorder import Recorder
from .model.signal import Signal
from .ports.sink import Sink
from .ports.system_clock import SystemClock
from .timing import hours_until, is_quiet, parse_range

__version__ = "0.8.0"

__all__ = [
    "FEEDBACK_STATES",
    "GATES",
    "GATE_RULES",
    "Gate",
    "ReasonCode",
    "REASONS",
    "SEVERITY_RANK",
    "VERBS",
    "ScoreBreakdown",
    "Clock",
    "Context",
    "AttentionDecision",
    "Feedback",
    "Intent",
    "NullSink",
    "Recorder",
    "Signal",
    "Sink",
    "SystemClock",
    "cost_of_waiting",
    "decide_attention",
    "decide_one",
    "dedupe_key",
    "hours_until",
    "is_quiet",
    "parse_range",
    "rollup",
    "score",
    "trace_id",
    "undo_hint",
]
