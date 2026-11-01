"""LAIX app kit: optional integration for apps.

This surface contains attention, execution, records, delivery, platform and
bench. It is useful for apps, but it is not the decision core. Persistent
memory, ingestion, proactivity, permissions and missions belong to the host.
"""

from .attention import (
    Context,
    Feedback,
    OutcomeLog,
    Signal,
    decide as decide_attention,
    is_quiet,
    score,
)
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
from .runtime import (
    ApprovalRequired,
    Budget,
    CallableDetector,
    DecisionRuntime,
    Detection,
    Detector,
    ExecutionBridge,
    ExperienceState,
    InMemoryStateStore,
    LiveContext,
    PerceptionEvent,
    PerceptionFrame,
    ResourcePlan,
    ResourcePolicy,
    SensingOption,
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
    "Context",
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
    "Feedback",
    "InMemoryPlatform",
    "InMemoryStateStore",
    "Layer",
    "LayerDecision",
    "LiveContext",
    "NullDelivery",
    "OutcomeLog",
    "PerceptionEvent",
    "PerceptionFrame",
    "Platform",
    "Proposal",
    "RecordEvidenceRef",
    "ResourcePlan",
    "ResourcePolicy",
    "SensingOption",
    "Signal",
    "SkillCall",
    "StateStore",
    "UnknownAction",
    "apply_proposal",
    "approve_proposal",
    "approve_record",
    "create_record",
    "decide_attention",
    "is_quiet",
    "mark_executed",
    "reject_proposal",
    "reject_record",
    "score",
    "undo_proposal",
    "verify_record",
]
