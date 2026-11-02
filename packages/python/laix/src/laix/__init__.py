"""LAIX: a domain-neutral decision layer.

The package answers one question for a live application: *given what is
happening, what the app is trying to achieve, what it can afford and what needs
approval, should it wait, observe, guide, ask, act, verify or escalate?*

It is intentionally standard-library only.  The host application provides
domain adapters; the decision layer never imports them.
"""

from .core import RECORD_NAMES
from .core.decisions import (
    ActionOption,
    Belief,
    CONSTRAINT_KINDS,
    Constraint,
    Decision,
    DecisionRequest,
    EvidenceRef,
    Goal,
    HORIZONS,
    Intent,
    Observation,
    PHASES,
    EXECUTION_RECEIPT_STATUSES,
    ExecutionReceipt,
    Situation,
    Trace,
)
from .core.outcome.record import OUTCOME_DIRECTIONS, OUTCOME_LABELS
from .core.outcome import Outcome
from .core.support.time import iso, parse_iso, utcnow
from .core.support.values import confidence_band
from .core.support.verbs import VERBS
from .core.support.version import SCHEMA_VERSION
from .core import attention, evaluation
from .core.attention import AttentionDecision, AttentionOutcome, Context, Feedback, Signal, decide_attention
from .appkit.delivery import DeliveryPort, DeliveryReceipt, NullDelivery
from .appkit.layer import Layer
from .core.evaluation import Case, Report, Row
from .core.evaluation import compare as compare_decisions
from .core.evaluation import load_cases
from .core.outcome import Arm, OutcomeLedger, OutcomeStore, UCBBandit, reward_for_label
from .appkit.platform import (
    ApprovalDecision,
    ApprovalRequest,
    CAPABILITY_LEVELS,
    Capability,
    PlatformEvent,
    InMemoryPlatform,
    Platform,
    SkillCall,
)
from .core.policies import (
    ActivePerceptionPolicy,
    AllocationPolicy,
    BanditPolicy,
    ActionPolicy,
    EscalationPolicy,
    NegotiationPolicy,
    ACTION_POLICY_VERSION,
    Policy,
    ActionPolicyConfig,
    PolicyError,
    PolicyRegistry,
    ActionPolicyRequest,
    PreferenceElicitationPolicy,
    ReplanningPolicy,
    SafetyConstrainedPolicy,
    VerificationPolicy,
    decide_action,
)
from .appkit.audit.decision_record import (
    DecisionRecord,
    EvidenceRef,
    approve as approve_record,
    create_record,
    mark_executed,
    reject as reject_record,
    verify as verify_record,
)
from .appkit.audit.proposal import Proposal, apply as apply_proposal, approve as approve_proposal, reject as reject_proposal, undo as undo_proposal
from .appkit.live_context import CallableDetector, LiveContext
from .appkit.runtime import (
    ApprovalRequired,
    DecisionRuntime,
    ExecutionBridge,
    ExperienceState,
    InMemoryStateStore,
    StateStore,
    UnknownAction,
)
from .core.perception import Detection, Detector, PerceptionEvent, PerceptionFrame
from .core.resources import Budget, ResourcePlan, ResourceScheduler, SensingOption

__all__ = [
    "ActionOption",
    "AttentionDecision",
    "AttentionOutcome",
    "ActivePerceptionPolicy",
    "AllocationPolicy",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalRequired",
    "Arm",
    "CAPABILITY_LEVELS",
    "Capability",
    "Case",
    "Context",
    "DecisionRecord",
    "DecisionRequest",
    "DeliveryPort",
    "DeliveryReceipt",
    "PlatformEvent",
    "EvidenceRef",
    "Feedback",
    "InMemoryPlatform",
    "InMemoryStateStore",
    "Layer",
    "LiveContext",
    "NullDelivery",
    "EscalationPolicy",
    "NegotiationPolicy",
    "OutcomeStore",
    "Platform",
    "Policy",
    "PolicyError",
    "PolicyRegistry",
    "Proposal",
    "Report",
    "Row",
    "Signal",
    "SkillCall",
    "StateStore",
    "apply_proposal",
    "approve_proposal",
    "approve_record",
    "attention",
    "compare_decisions",
    "create_record",
    "evaluation",
    "load_cases",
    "mark_executed",
    "reject_proposal",
    "reject_record",
    "reward_for_label",
    "undo_proposal",
    "verify_record",
    "Belief",
    "BanditPolicy",
    "Budget",
    "RECORD_NAMES",
    "CONSTRAINT_KINDS",
    "CallableDetector",
    "Constraint",
    "Decision",
    "ActionPolicy",
    "DecisionRuntime",
    "Detection",
    "Detector",
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
    "ACTION_POLICY_VERSION",
    "PerceptionEvent",
    "PerceptionFrame",
    "ActionPolicyConfig",
    "ActionPolicyRequest",
    "PreferenceElicitationPolicy",
    "EXECUTION_RECEIPT_STATUSES",
    "ExecutionReceipt",
    "ResourcePlan",
    "ResourceScheduler",
    "ReplanningPolicy",
    "SCHEMA_VERSION",
    "SafetyConstrainedPolicy",
    "SensingOption",
    "Situation",
    "Trace",
    "UCBBandit",
    "UnknownAction",
    "VERBS",
    "VerificationPolicy",
    "confidence_band",
    "decide_action",
    "decide_attention",
    "iso",
    "parse_iso",
    "utcnow",
]
