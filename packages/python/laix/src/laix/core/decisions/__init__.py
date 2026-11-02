"""The decision shapes: request, decision and normalisation into one answer.

``Decision`` and ``DecisionRequest`` are the two shapes a host and a policy
exchange. ``coerce`` and ``from_attention`` normalise any policy result into
the one public ``Decision``.
"""

from __future__ import annotations

from ..support.verbs import VERBS
from ..support.version import SCHEMA_VERSION
from .request import (
    HORIZONS,
    PHASES,
    ActionOption,
    Belief,
    CONSTRAINT_KINDS,
    Constraint,
    DecisionRequest,
    Goal,
    Observation,
    Situation,
)
from .answer import EvidenceRef, Intent, ScoreBreakdown
from .normalise import coerce, from_attention
from .answer.decision import Decision
from .lifecycle.execution_receipt import EXECUTION_RECEIPT_STATUSES, ExecutionReceipt
from .lifecycle.trace import Trace

__all__ = [
    "ActionOption",
    "Belief",
    "ScoreBreakdown",
    "CONSTRAINT_KINDS",
    "Constraint",
    "Decision",
    "DecisionRequest",
    "EvidenceRef",
    "Goal",
    "HORIZONS",
    "Intent",
    "Observation",
    "PHASES",
    "EXECUTION_RECEIPT_STATUSES",
    "ExecutionReceipt",
    "SCHEMA_VERSION",
    "Situation",
    "Trace",
    "VERBS",
    "coerce",
    "from_attention",
]
