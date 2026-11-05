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
from .response import EvidenceRef, Intent, ScoreBreakdown
from .normalise import coerce, from_attention
from .response.decision import DECISION_STATUSES, TARGET_MODES, Decision
from .trail.execution_receipt import EXECUTION_RECEIPT_STATUSES, ExecutionReceipt
from .trail.trace import Trace

__all__ = [
    "ActionOption",
    "Belief",
    "ScoreBreakdown",
    "CONSTRAINT_KINDS",
    "Constraint",
    "Decision",
    "DecisionRequest",
    "DECISION_STATUSES",
    "TARGET_MODES",
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
