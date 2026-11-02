"""LAIX: a domain-neutral decision layer.

The package answers one question for a live application: *given what is
happening, what the app is trying to achieve, what it can afford and what needs
approval, should it wait, observe, guide, ask, act, verify or escalate?*

It is intentionally standard-library only.  The host application provides
domain adapters; the decision layer never imports them.

A host that only needs the answer calls ``decide(request)``.  Execution,
records, delivery and the rest of the app kit are optional and load lazily.
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
from .core.outcome_learning.record import OUTCOME_DIRECTIONS, OUTCOME_LABELS
from .core.outcome_learning import AttentionOutcome, Outcome
from .core.support.time import iso, parse_iso, utcnow
from .core.support.values import confidence_band
from .core.support.verbs import VERBS, Verb
from .core.support.version import SCHEMA_VERSION
from .core import evaluation
from .core.engines import attention
from .core.engines.attention import AttentionDecision, Context, Feedback, Signal, decide_attention
from .core.evaluation import Case, Report, Row
from .core.evaluation import compare as compare_decisions
from .core.evaluation import load_cases
from .core.outcome_learning import AttentionOutcome, Arm, OutcomeLedger, OutcomeStore, UCBBandit, reward_for_label
from .core.engines.policies import (
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
from .core.sensing import Detection, Detector, PerceptionEvent, PerceptionFrame
from .core.engines.resources import Budget, ResourcePlan, ResourceScheduler, SensingOption
from .core.dispatch import decide, select

# The app kit is optional and is imported on first use.  A host that only needs
# the decision core can ``import laix.core`` or ``from laix import Decision`` and
# never load execution, records, delivery or the platform surface.
_APPKIT_NAMES: dict[str, dict[str, str]] = {
    ".appkit.audit": {
        "Approval": "Approval",
        "AuditEvent": "AuditEvent",
        "Undo": "Undo",
    },
    ".appkit.audit.decision_record": {
        "DecisionRecord": "DecisionRecord",
        "approve_record": "approve",
        "create_record": "create_record",
        "mark_executed": "mark_executed",
        "reject_record": "reject",
        "verify_record": "verify",
    },
    ".appkit.audit.proposal": {
        "Proposal": "Proposal",
        "apply_proposal": "apply",
        "approve_proposal": "approve",
        "reject_proposal": "reject",
        "undo_proposal": "undo",
    },
    ".appkit.delivery": {
        "DeliveryPort": "DeliveryPort",
        "DeliveryReceipt": "DeliveryReceipt",
        "NullDelivery": "NullDelivery",
    },
    ".appkit.layer": {"Layer": "Layer"},
    ".appkit.live_context": {
        "CallableDetector": "CallableDetector",
        "LiveContext": "LiveContext",
    },
    ".appkit.platform": {
        "ApprovalDecision": "ApprovalDecision",
        "ApprovalRequest": "ApprovalRequest",
        "CAPABILITY_LEVELS": "CAPABILITY_LEVELS",
        "Capability": "Capability",
        "InMemoryPlatform": "InMemoryPlatform",
        "Platform": "Platform",
        "PlatformEvent": "PlatformEvent",
        "SkillCall": "SkillCall",
    },
    ".appkit.runtime": {
        "ApprovalRequired": "ApprovalRequired",
        "DecisionRuntime": "DecisionRuntime",
        "ExecutionBridge": "ExecutionBridge",
        "ExperienceState": "ExperienceState",
        "InMemoryStateStore": "InMemoryStateStore",
        "StateStore": "StateStore",
        "UnknownAction": "UnknownAction",
    },
}
_APPKIT_LOOKUP: dict[str, tuple[str, str]] = {
    name: (module, attribute)
    for module, names in _APPKIT_NAMES.items()
    for name, attribute in names.items()
}


def __getattr__(name: str):
    """Load an app kit name only when it is actually requested."""
    entry = _APPKIT_LOOKUP.get(name)
    if entry is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_path, attribute = entry
    from importlib import import_module

    value = getattr(import_module(module_path, __name__), attribute)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_APPKIT_LOOKUP))


__all__ = [
    "ActionOption",
    "AttentionDecision",
    "AttentionOutcome",
    "ActivePerceptionPolicy",
    "AllocationPolicy",
    "Approval",
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalRequired",
    "AuditEvent",
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
    "Undo",
    "VERBS",
    "Verb",
    "VerificationPolicy",
    "confidence_band",
    "decide",
    "decide_action",
    "decide_attention",
    "iso",
    "parse_iso",
    "select",
    "utcnow",
]
