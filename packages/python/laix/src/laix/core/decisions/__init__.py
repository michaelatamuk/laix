"""The decision shapes: request, decision and normalisation into one answer.

``Decision`` and ``DecisionRequest`` are the two shapes a host and a policy
exchange. ``coerce`` and ``from_attention`` normalise any policy result into
the one public ``Decision``.
"""

from __future__ import annotations

from ..verbs import VERBS
from ..version import SCHEMA_VERSION
from .action_option import ActionOption
from .belief import Belief
from .breakdown import Breakdown
from .constraint import CONSTRAINT_KINDS, Constraint
from .convert import coerce, from_attention
from .decision import Decision
from .decision_request import DecisionRequest
from .escalation import Escalation
from .evidence_ref import EvidenceRef
from .goal import Goal
from .intent import Intent
from .observation import Observation
from .receipt import RECEIPT_STATUSES, Receipt
from .situation import HORIZONS, PHASES, Situation
from .trace import Trace

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
