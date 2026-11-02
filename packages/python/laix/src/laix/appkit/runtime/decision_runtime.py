"""The runtime facade an app talks to.

``DecisionRuntime`` wires the five reusable pieces together:

    observe -> state -> policy -> execution -> outcome

Every decision gets a trace, every execution gets a receipt, and every measured
change is recorded against the decision that caused it.  The runtime is
in-process and dependency-free; a cloud service can persist the same records.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from ...core.decisions import (
    ActionOption,
    Decision,
    Observation,
    ExecutionReceipt,
    Situation,
    Trace,
)
from ...core.support.ids import new_id
from ...core.outcome_learning import Outcome
from ...core.support.time import iso
from .execution import ApprovalRequired, ExecutionBridge
from ...core.outcome_learning import OutcomeLedger
from ...core.engines.policies.implementations.action import ActionPolicy, ActionPolicyRequest
from ...core.engines.resources import Budget, ResourcePlan, ResourceScheduler, SensingOption
from .state import ExperienceState

IdFactory = Callable[[str], str]


class DecisionRuntime:
    def __init__(
        self,
        *,
        state: ExperienceState | None = None,
        policy: ActionPolicy | None = None,
        bridge: ExecutionBridge | None = None,
        outcomes: OutcomeLedger | None = None,
        resources: ResourceScheduler | None = None,
        id_factory: IdFactory | None = None,
    ) -> None:
        self.state = state or ExperienceState(subject="")
        self.policy = policy or ActionPolicy()
        self.bridge = bridge or ExecutionBridge()
        self.outcomes = outcomes or OutcomeLedger()
        self.resources = resources or ResourceScheduler()
        self._id = id_factory or new_id
        self._actions: dict[str, ActionOption] = {}
        self._decisions: dict[str, Decision] = {}
        self._traces: dict[str, Trace] = {}
        self._trace_by_decision: dict[str, str] = {}
        self._receipts: list[str] = []

    # ------------------------------------------------------------------ decide
    def observe(self, observation: Observation) -> None:
        self.state.observe(observation)

    def decide(
        self,
        situation: Situation,
        options: Iterable[ActionOption],
        *,
        attributes: dict[str, Any] | None = None,
    ) -> Decision:
        decision_id = self._id("DEC")
        trace_id = self._id("TRC")
        request = ActionPolicyRequest(situation=situation, options=tuple(options), attributes=dict(attributes or {}))
        decision = self.policy.decide(request, decision_id=decision_id, trace_id=trace_id)
        self._decisions[decision.decision_id] = decision
        for option in request.options:
            self._actions[option.id] = option
        self.state.record(decision)
        self._traces[trace_id] = Trace(id=trace_id, decision_id=decision.decision_id).with_event(
            "situation",
            {
                "subject": situation.subject,
                "phase": situation.phase,
                "horizon": situation.horizon,
                "confidence": round(situation.confidence(), 4),
                "observations": len(situation.observations),
                "beliefs": len(situation.beliefs),
                "options": [item.id for item in request.options],
                "attributes": {**situation.attributes, **request.attributes},
            },
            at=situation.at,
        )
        self._append_trace(
            decision,
            "decided",
            {
                "verb": decision.verb,
                "action": decision.action_id,
                "rationale": decision.rationale,
                "policy": decision.policy_version,
                "requiresApproval": decision.requires_approval,
            },
        )
        self._trace_by_decision[decision.decision_id] = trace_id
        return decision

    # ---------------------------------------------------------------- execute
    def execute(
        self,
        decision: Decision,
        *,
        actor: str,
        approver: str | None = None,
        context: dict[str, Any] | None = None,
        action: ActionOption | None = None,
    ) -> ExecutionReceipt:
        resolved = action or (self._actions.get(decision.action_id) if decision.action_id else None)
        try:
            receipt = self.bridge.execute(decision, action=resolved, actor=actor, approver=approver, context=context)
        except ApprovalRequired as exc:
            receipt = self.bridge.refuse(decision, action=resolved, actor=actor, reason=str(exc))
            self._append_trace(decision, "approval.required", {"actor": actor, "reason": str(exc)})
        self._receipts.append(receipt.id)
        self._append_trace(
            decision,
            f"execution.{receipt.status}",
            {"receipt": receipt.id, "actor": actor, "approvedBy": approver, "error": receipt.error},
        )
        return receipt

    def cancel(self, receipt_id: str, *, actor: str, reason: str = "") -> ExecutionReceipt:
        receipt = self.bridge.cancel(receipt_id, actor=actor, reason=reason)
        decision = self._decisions.get(receipt.decision_id)
        if decision:
            self._append_trace(decision, "execution.cancelled", {"receipt": receipt.id, "actor": actor, "reason": reason})
        return receipt

    def undo(self, receipt_id: str, *, actor: str) -> ExecutionReceipt:
        receipt = self.bridge.undo(receipt_id, actor=actor)
        decision = self._decisions.get(receipt.decision_id)
        if decision:
            self._append_trace(decision, "execution.undone", {"receipt": receipt.id, "actor": actor})
        return receipt

    # ---------------------------------------------------------------- outcome
    def measure(
        self,
        decision_id: str,
        *,
        metric: str,
        before: float,
        after: float,
        attributed: bool = False,
        direction: str = "higher-better",
        evidence: dict[str, Any] | None = None,
        note: str = "",
        label: str | None = None,
    ) -> Outcome:
        outcome = self.outcomes.record(
            decision_id,
            metric=metric,
            before=before,
            after=after,
            attributed=attributed,
            direction=direction,
            evidence=evidence,
            note=note,
            label=label,
        )
        decision = self._decisions.get(decision_id)
        if decision:
            self._append_trace(
                decision,
                "outcome.measured",
                {"metric": metric, "delta": outcome.delta, "label": outcome.label, "attributed": attributed},
            )
        return outcome

    # --------------------------------------------------------------- resource
    def schedule(self, options: Iterable[SensingOption], *, budget: Budget | None = None, uncertainty: float | None = None) -> ResourcePlan:
        if uncertainty is None:
            confidence = self.state.confidence()
            uncertainty = 1.0 - confidence if confidence > 0 else 0.5
        plan = self.resources.schedule(options, budget=budget, uncertainty=uncertainty)
        self.state.history.append(
            {"at": iso(), "event": "resource.plan", "allowed": list(plan.allowed), "deepCalls": plan.deep_calls}
        )
        return plan

    # ------------------------------------------------------------------ trace
    def trace(self, decision_id: str) -> Trace:
        trace_id = self._trace_by_decision.get(decision_id)
        if not trace_id:
            raise KeyError(decision_id)
        return self._traces[trace_id]

    def decision(self, decision_id: str) -> Decision:
        return self._decisions[decision_id]

    def action_for(self, decision: Decision) -> ActionOption | None:
        if not decision.action_id:
            return None
        return self._actions.get(decision.action_id)

    def receipts(self) -> list[ExecutionReceipt]:
        return [self.bridge.get(receipt_id) for receipt_id in self._receipts]

    def stats(self) -> dict[str, Any]:
        verbs = Counter(item.verb for item in self._decisions.values())
        statuses = Counter(item.status for item in self.receipts())
        return {
            "decisions": len(self._decisions),
            "verbs": dict(sorted(verbs.items())),
            "executions": dict(sorted(statuses.items())),
            "outcomes": self.outcomes.summary(),
            "policyVersion": self.policy.version,
        }

    def _append_trace(self, decision: Decision, stage: str, detail: dict[str, Any] | None = None) -> None:
        trace_id = decision.trace_id
        trace = self._traces.get(trace_id)
        if trace is None:
            trace = Trace(id=trace_id or self._id("TRC"), decision_id=decision.decision_id)
        self._traces[trace.id] = trace.with_event(stage, detail)
        self._trace_by_decision[decision.decision_id] = trace.id
