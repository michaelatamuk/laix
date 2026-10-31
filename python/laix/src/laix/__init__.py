"""LAIX: a domain-neutral decision layer.

The package answers one question for a live application: *given what is
happening, what the app is trying to achieve, what it can afford and what needs
approval, should it wait, observe, guide, ask, act, verify or escalate?*

It is intentionally standard-library only.  The host application provides
domain adapters; the decision layer never imports them.
"""

from .contracts import (
    CONTRACT_NAMES,
    CONTRACTS,
    CONSTRAINT_KINDS,
    HORIZONS,
    OUTCOME_DIRECTIONS,
    OUTCOME_LABELS,
    PHASES,
    RECEIPT_STATUSES,
    SCHEMA_VERSION,
    VERBS,
    Action,
    Belief,
    Constraint,
    Decision,
    Goal,
    Observation,
    Outcome,
    Receipt,
    Situation,
    Trace,
    confidence_band,
    iso,
    parse_iso,
    utcnow,
)
from . import attention, evaluation
from .attention import Context, Feedback, Signal
from .delivery import DeliveryPort, DeliveryReceipt, NullDelivery
from .evaluation import Case, Report, Row
from .evaluation import compare as compare_decisions
from .evaluation import load_cases
from .execution import ApprovalRequired, ExecutionBridge, UnknownAction
from .layer import Decision as LayerDecision
from .layer import DecisionRequest, Layer
from .outcome import OutcomeLedger
from .policies import Policy, PolicyError, PolicyRegistry
from .proposal import Proposal, apply as apply_proposal, approve as approve_proposal, reject as reject_proposal, undo as undo_proposal
from .record import DecisionRecord, approve as approve_record, create_record, reject as reject_record, verify as verify_record
from .policy import POLICY_VERSION, DecisionPolicy, PolicyConfig, PolicyRequest, decide
from .resources import Budget, ResourcePlan, ResourcePolicy, SensingOption
from .runtime import DecisionRuntime
from .state import ExperienceState

__all__ = [
    "Action",
    "ApprovalRequired",
    "Case",
    "Context",
    "DecisionRecord",
    "DecisionRequest",
    "DeliveryPort",
    "DeliveryReceipt",
    "Feedback",
    "Layer",
    "LayerDecision",
    "NullDelivery",
    "Policy",
    "PolicyError",
    "PolicyRegistry",
    "Proposal",
    "Report",
    "Row",
    "Signal",
    "apply_proposal",
    "approve_proposal",
    "approve_record",
    "attention",
    "compare_decisions",
    "create_record",
    "evaluation",
    "load_cases",
    "reject_proposal",
    "reject_record",
    "undo_proposal",
    "verify_record",
    "Belief",
    "Budget",
    "CONTRACT_NAMES",
    "CONTRACTS",
    "CONSTRAINT_KINDS",
    "Constraint",
    "Decision",
    "DecisionPolicy",
    "DecisionRuntime",
    "ExecutionBridge",
    "ExperienceState",
    "Goal",
    "HORIZONS",
    "Observation",
    "Outcome",
    "OutcomeLedger",
    "OUTCOME_DIRECTIONS",
    "OUTCOME_LABELS",
    "PHASES",
    "POLICY_VERSION",
    "PolicyConfig",
    "PolicyRequest",
    "RECEIPT_STATUSES",
    "Receipt",
    "ResourcePlan",
    "ResourcePolicy",
    "SCHEMA_VERSION",
    "SensingOption",
    "Situation",
    "Trace",
    "UnknownAction",
    "VERBS",
    "confidence_band",
    "decide",
    "iso",
    "parse_iso",
    "utcnow",
]
