"""LAIX attention — a small, domain-free decision layer for the right moment.

Given a candidate intervention, the current context and the user's limits,
should the product **wait, observe, guide, ask, act, verify or escalate**?

A generic policy inside LAIX. No framework, no agent runtime, no app types, no
network, no database, no clock of its own.
"""

from __future__ import annotations

from ..decisions import Breakdown, Intent
from ..support.verbs import VERBS
from .model.decision import AttentionDecision
from .model.outcome import AttentionOutcome
from .ports.clock import Clock
from .model.context import Context
from .model.feedback import Feedback
from .labels import (
    FEEDBACK_STATES,
    HELPED,
    HURT,
    NEUTRAL,
    REASON_CODES,
    RESULTS,
    SEVERITY_RANK,
    UNKNOWN,
    label_for_feedback,
    result_for_reason,
)
from .ports.null_sink import NullSink
from .outcome_log import OutcomeLog
from .decide import decide_attention, decide_one, dedupe_key, rollup, trace_id
from .gates import GATES, REASONS, feedback_blocks, rank
from .score import SEVERITY_POINTS, WAIT_FACTOR, cost_of_waiting, score, undo_hint
from .ports.recorder import Recorder
from .replay import (
    POLICIES,
    benchmark,
    compare,
    context_from,
    load_vectors,
    precision_recall,
    run_case,
    run_vectors,
    signal_from,
    validate_document,
)
from .model.signal import Signal
from .ports.sink import Sink
from .ports.system_clock import SystemClock
from .timing import hours_until, is_quiet, parse_range

__version__ = "0.8.0"

__all__ = [
    "FEEDBACK_STATES",
    "GATES",
    "HELPED",
    "HURT",
    "NEUTRAL",
    "POLICIES",
    "REASONS",
    "REASON_CODES",
    "RESULTS",
    "SEVERITY_RANK",
    "UNKNOWN",
    "VERBS",
    "Breakdown",
    "Clock",
    "Context",
    "AttentionDecision",
    "AttentionOutcome",
    "Feedback",
    "Intent",
    "NullSink",
    "OutcomeLog",
    "Recorder",
    "Signal",
    "Sink",
    "SystemClock",
    "benchmark",
    "compare",
    "context_from",
    "cost_of_waiting",
    "decide_attention",
    "decide_one",
    "dedupe_key",
    "hours_until",
    "is_quiet",
    "label_for_feedback",
    "load_vectors",
    "parse_range",
    "precision_recall",
    "result_for_reason",
    "rollup",
    "run_case",
    "run_vectors",
    "score",
    "signal_from",
    "trace_id",
    "undo_hint",
    "validate_document",
]
