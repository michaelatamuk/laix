"""LAIX signal attention - a small, domain-free decision layer for the right moment.

Given a candidate intervention, the current context and the user's limits,
should the product **wait, observe, guide, ask, act, verify or escalate**?

A generic policy inside LAIX. No framework, no agent runtime, no app types, no
network, no database, no clock of its own.
"""

from __future__ import annotations

from ...decisions import ScoreBreakdown, Intent
from ...support.verbs import VERBS
from .output.signal_attention_decision import SignalAttentionDecision
from .input.signal_context import SignalContext
from .input.signal_feedback import FEEDBACK_STATES, SignalFeedback
from .input.severity import SEVERITY_RANK
from .decide import decide_signal_attention, decide_one, dedupe_key, rollup, trace_id
from .gates import GATES, GATE_RULES, REASONS, Gate, ReasonCode, feedback_blocks, rank
from .score import SEVERITY_POINTS, WAIT_FACTOR, cost_of_waiting, score
from .output.undo import undo_hint
from .input.signal import Signal
from .timing import hours_until, is_quiet, parse_range

__version__ = "0.8.0"

__all__ = [
    "FEEDBACK_STATES",
    "GATES",
    "GATE_RULES",
    "Gate",
    "ReasonCode",
    "REASONS",
    "SEVERITY_POINTS",
    "SEVERITY_RANK",
    "VERBS",
    "WAIT_FACTOR",
    "ScoreBreakdown",
    "SignalContext",
    "SignalAttentionDecision",
    "SignalFeedback",
    "Intent",
    "Signal",
    "cost_of_waiting",
    "decide_signal_attention",
    "decide_one",
    "dedupe_key",
    "feedback_blocks",
    "hours_until",
    "is_quiet",
    "parse_range",
    "rank",
    "rollup",
    "score",
    "trace_id",
    "undo_hint",
]
