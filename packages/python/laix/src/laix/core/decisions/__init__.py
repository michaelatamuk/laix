"""The decision shapes: request, decision and normalisation into one answer.

``Decision`` and ``DecisionRequest`` are the two shapes a host and a policy
exchange. ``coerce`` and ``from_attention`` normalise any policy result into
the one public ``Decision``.
"""

from __future__ import annotations

from ..support.verbs import VERBS
from ..support.version import SCHEMA_VERSION
from .request.action_option import ActionOption
from .request.belief import Belief
from .answer.breakdown import Breakdown
from .request.constraint import CONSTRAINT_KINDS, Constraint
from .normalise import coerce, from_attention
from .answer.decision import Decision
from .request.decision_request import DecisionRequest
from .answer.escalation import Escalation
from .answer.evidence_ref import EvidenceRef
from .request.goal import Goal
from .answer.intent import Intent
from .request.observation import Observation
from .lifecycle.receipt import RECEIPT_STATUSES, Receipt
from .request.situation import HORIZONS, PHASES, Situation
from .lifecycle.trace import Trace

__all__ = [
    "ActionOption",
    "Belief",
    "Breakdown",
    "CONSTRAINT_KINDS",
    "Constraint",
    "Decision",
    "DecisionRequest",
    "Escalation",
    "EvidenceRef",
    "Goal",
    "HORIZONS",
    "Intent",
    "Observation",
    "PHASES",
    "RECEIPT_STATUSES",
    "Receipt",
    "SCHEMA_VERSION",
    "Situation",
    "Trace",
    "VERBS",
    "coerce",
    "from_attention",
]
