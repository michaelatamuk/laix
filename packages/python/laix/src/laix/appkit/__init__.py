"""LAIX app kit: optional integration for apps.

This surface contains execution, records, delivery, platform, live context and
bench. It is useful for apps, but it is not the decision core. Persistent
memory, ingestion, proactivity, permissions and missions belong to the host.
"""

from .delivery import DeliveryPort, DeliveryReceipt, NullDelivery
from .layer import Decision, DecisionRequest, Layer
from .platform import (
    ApprovalDecision,
    ApprovalRequest,
    CAPABILITY_LEVELS,
    Capability,
    PlatformEvent,
    InMemoryPlatform,
    Platform,
    SkillCall,
)
from .audit.decision_record import (
    DecisionRecord,
    EvidenceRef,
    approve as approve_record,
    create_record,
    mark_executed,
    reject as reject_record,
    verify as verify_record,
)
from .audit.proposal import (
    Proposal,
    apply as apply_proposal,
    approve as approve_proposal,
    reject as reject_proposal,
    undo as undo_proposal,
)
from ..core.sensing import Detection, Detector, PerceptionEvent, PerceptionFrame
from ..core.engines.resources import Budget, ResourcePlan, ResourceScheduler, SensingOption
from .live_context import CallableDetector, LiveContext
from .runtime import (
    ApprovalRequired,
    DecisionRuntime,
    ExecutionBridge,
    ExperienceState,
    InMemoryStateStore,
    StateStore,
    UnknownAction,
)

__all__ = [
    "ApprovalDecision",
    "ApprovalRequest",
    "ApprovalRequired",
    "Budget",
    "CAPABILITY_LEVELS",
    "CallableDetector",
    "Capability",
    "DecisionRecord",
    "DecisionRequest",
    "DecisionRuntime",
    "DeliveryPort",
    "DeliveryReceipt",
    "Detection",
    "Detector",
    "PlatformEvent",
    "EvidenceRef",
    "ExecutionBridge",
    "ExperienceState",
    "InMemoryPlatform",
    "InMemoryStateStore",
    "Layer",
    "LiveContext",
    "NullDelivery",
    "PerceptionEvent",
    "PerceptionFrame",
    "Platform",
    "Proposal",
    "EvidenceRef",
    "ResourcePlan",
    "ResourceScheduler",
    "SensingOption",
    "SkillCall",
    "StateStore",
    "UnknownAction",
    "apply_proposal",
    "approve_proposal",
    "approve_record",
    "create_record",
    "mark_executed",
    "reject_proposal",
    "reject_record",
    "undo_proposal",
    "verify_record",
]