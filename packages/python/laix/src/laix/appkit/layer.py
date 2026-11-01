"""The public Layer: one request in, one decision shape out.

The decision types live in ``laix.core.decisions``. This module keeps the orchestrator
and re-exports the public types so existing imports from ``laix.layer`` keep
working.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from . import attention
from ..core.contracts import SCHEMA_VERSION
from ..core.contracts import Decision as CoreDecision
from ..core.decisions import (
    Breakdown,
    Decision,
    DecisionRequest,
    Escalation,
    EvidenceRef,
    Intent,
    coerce,
    from_attention,
    from_core,
)
from .delivery import DeliveryPort, DeliveryReceipt
from ..core.policies import Policy, PolicyRegistry
from ..core.policies.action import POLICY_VERSION
from .runtime import DecisionRuntime
from .runtime.execution import ExecutionBridge


class Layer:
    """The single object an app talks to."""

    def __init__(self, runtime: DecisionRuntime | None = None, policy: Policy | None = None) -> None:
        self.runtime = runtime or DecisionRuntime()
        self._core_decisions: dict[str, CoreDecision] = {}
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
        if self._policy is not None:
            decisions = [coerce(item) for item in self._policy.decide(request)]
            self._decisions.extend(decisions)
            return decisions

        if request.situation is not None or request.options:
            if request.situation is None:
                raise ValueError("action selection needs a situation")
            decision = self.runtime.decide(request.situation, request.options, attributes=request.attributes)
            self._core_decisions[decision.id] = decision
            result = [from_core(decision)]
        else:
            if request.context is None:
                raise ValueError("attention allocation needs a context with now")
            result = [from_attention(item) for item in attention.decide(request.signals, request.context)]
        self._decisions.extend(result)
        return result

    def execute(
        self,
        decision: Decision,
        *,
        actor: str,
        approver: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Any:
        core = self._core_decisions.get(decision.decision_id)
        if core is None:
            raise ValueError("this decision has no executable action in this layer")
        return self.runtime.execute(core, actor=actor, approver=approver, context=context)

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
        version = getattr(self._policy, "version", None) if self._policy is not None else POLICY_VERSION
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
    "Breakdown",
    "Decision",
    "DecisionRequest",
    "Escalation",
    "EvidenceRef",
    "Intent",
    "Layer",
    "from_attention",
    "from_core",
]
