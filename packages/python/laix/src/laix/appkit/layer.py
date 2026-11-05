"""The public Layer: one request in, one decision shape out.

This module keeps the orchestrator, the built-in request routing and the
normalisation of custom policy results into the one ``Decision`` shape.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..core.support.version import SCHEMA_VERSION
from ..core.decisions import (
    ScoreBreakdown,
    Decision,
    DecisionRequest,
    EvidenceRef,
    Intent,
)
from ..core.dispatch import (
    annotate_confidence,
    attributes_for,
    decide as decide_core,
    select,
)
from .delivery import DeliveryPort, DeliveryReceipt
from ..core.engines.policies import Policy, PolicyRegistry
from ..core.engines.policies.implementations.action import ACTION_POLICY_VERSION
from .runtime import DecisionRuntime
from .runtime.execution import ExecutionBridge
from .streaming import StreamSession


class Layer:
    """The single object an app talks to."""

    def __init__(self, runtime: DecisionRuntime | None = None, policy: Policy | None = None) -> None:
        self.runtime = runtime or DecisionRuntime()
        self._decisions: list[Decision] = []
        self._registry = PolicyRegistry()
        self._policy: Policy | None = None
        if policy is not None:
            name = str(getattr(policy, "name", "custom"))
            self._registry.register(name, policy)
            self._policy = policy

    def register_policy(self, name: str, policy: Policy) -> None:
        self._registry.register(name, policy)

    def use_policy(self, name: str) -> None:
        self._policy = self._registry.get(name)

    def policies(self) -> tuple[str, ...]:
        return self._registry.names()

    def decide(self, request: DecisionRequest) -> list[Decision]:
        route = select(request, self._policy)
        if route == "action":
            if request.situation is None:
                raise ValueError("action selection needs a situation")
            decision = self.runtime.decide(
                request.situation,
                request.options,
                attributes=attributes_for(request),
            )
            result = [annotate_confidence(decision, request)]
        elif route == "policy":
            result = decide_core(request, self._policy)
        else:
            result = decide_core(request)
        self._decisions.extend(result)
        return result

    def stream(self, **options: Any) -> StreamSession:
        """Create a stream session backed by this layer's decision path."""
        return StreamSession(self.decide, **options)

    def execute(
        self,
        decision: Decision,
        *,
        actor: str,
        approver: str | None = None,
        context: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        return self.runtime.execute(
            decision,
            actor=actor,
            approver=approver,
            context=context,
            idempotency_key=idempotency_key,
        )

    def measure(self, decision: Decision, **kwargs: Any) -> Any:
        return self.runtime.measure(decision.decision_id, **kwargs)

    def deliver(
        self,
        decision: Decision,
        port: DeliveryPort,
        message: Any,
        *,
        channel: str = "default",
    ) -> DeliveryReceipt:
        return port.deliver(decision, message, channel=channel)

    def status(self) -> dict[str, Any]:
        policy = getattr(self._policy, "name", None) if self._policy is not None else "builtin"
        version = getattr(self._policy, "version", None) if self._policy is not None else ACTION_POLICY_VERSION
        return {
            "schemaVersion": SCHEMA_VERSION,
            "policy": policy,
            "policyVersion": version,
            "decisions": len(self._decisions),
            "policies": self._registry.names(),
        }

    def explain(self, decision: Decision) -> dict[str, Any]:
        return {
            "verb": decision.verb,
            "reasonCode": decision.reason_code,
            "rationale": decision.rationale,
            "confidence": decision.confidence,
            "evidence": [asdict(item) for item in decision.evidence],
            "score": decision.score,
            "breakdown": asdict(decision.breakdown) if decision.breakdown else None,
            "requiresApproval": decision.requires_approval,
            "deliver": decision.deliver,
            "record": decision.record,
            "traceId": decision.trace_id,
        }

    def bridge(self) -> ExecutionBridge:
        return self.runtime.bridge


__all__ = [
    "ScoreBreakdown",
    "Decision",
    "DecisionRequest",
    "EvidenceRef",
    "Intent",
    "Layer",
]
