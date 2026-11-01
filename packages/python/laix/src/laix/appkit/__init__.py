"""LAIX app kit: optional integration for apps.

This surface contains execution, records, delivery, platform, live context and
bench. It is useful for apps, but it is not the decision core. Persistent
memory, ingestion, proactivity, permissions and missions belong to the host.
"""

from .delivery import DeliveryPort, DeliveryReceipt, NullDelivery
from .layer import Decision as LayerDecision
from .layer import DecisionRequest, Layer
from .platform import (
    ApprovalDecision,
    ApprovalRequest,
    CAPABILITY_LEVELS,
    Capability,
    Event,
    InMemoryPlatform,
    Platform,
    SkillCall,
)
from .records.decision import (
    DecisionRecord,
    EvidenceRef as RecordEvidenceRef,
    approve as approve_record,
    create_record,
    mark_executed,
    reject as reject_record,
    verify as verify_record,
)
from .records.proposal import (
    Proposal,
    apply as apply_proposal,
    approve as approve_proposal,
    reject as reject_proposal,
    undo as undo_proposal,
)
from ..core.perception import Detection, Detector, PerceptionEvent, PerceptionFrame
from ..core.resources import Budget, ResourcePlan, ResourcePolicy, SensingOption
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
    "Event",
    "EvidenceRef",
    "ExecutionBridge",
    "ExperienceState",
    "InMemoryPlatform",
    "InMemoryStateStore",
    "Layer",
    "LayerDecision",
    "LiveContext",
    "NullDelivery",
    "PerceptionEvent",
    "PerceptionFrame",
    "Platform",
    "Proposal",
    "RecordEvidenceRef",
    "ResourcePlan",
    "ResourcePolicy",
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