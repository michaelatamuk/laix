"""The built-in action policy: version, config, request and policy.

Config and request live here because they exist only for this policy.
"""

from __future__ import annotations

from typing import Any

from ....decisions import ActionOption, Decision, Situation
from ....support.time import iso
from ....support.values import clamp
from ....support.verbs import Verb
from .action_policy_config import ActionPolicyConfig
from .action_policy_input import ActionPolicyInput


ACTION_POLICY_VERSION = "0.8.0"


def _number(payload: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "required", "always", "blocked", "on"}
    return bool(value)


class ActionPolicy:
    def __init__(self, config: ActionPolicyConfig | None = None) -> None:
        self.config = config or ActionPolicyConfig()
        self.version = ACTION_POLICY_VERSION

    # ------------------------------------------------------------------ decide
    def decide(
        self,
        request: ActionPolicyInput,
        *,
        decision_id: str = "",
        trace_id: str = "",
        created_at: str | None = None,
    ) -> Decision:
        situation = request.situation
        attributes = {**situation.attributes, **request.attributes}
        applied: list[str] = []
        blocked: dict[str, str] = {}

        admitted = self._admit(situation, request.options, applied, blocked)
        by_verb = {verb: [item for item in admitted if item.verb == verb] for verb in Verb}

        confidence = situation.confidence()
        if "confidence" in attributes:
            confidence = clamp(_number(attributes, "confidence", confidence))
        uncertainty = _number(attributes, "uncertainty", 1.0 - confidence)
        urgency = _number(attributes, "urgency", 0.5)
        deadline_breached = _truthy(attributes.get("deadline_breached", False))
        safety_breached = _truthy(attributes.get("safety_breached", False))
        verification_due = _truthy(attributes.get("verification_due", False))
        needs_more_info = _truthy(attributes.get("needs_more_info", False))

        verb: str
        chosen: ActionOption | None = None
        rationale: str

        if self._safety_blocked(situation):
            verb, rationale = Verb.WAIT, "hard safety constraint blocks action"
        elif (deadline_breached or safety_breached) and by_verb[Verb.ESCALATE]:
            verb, chosen = Verb.ESCALATE, self._best(by_verb[Verb.ESCALATE])
            rationale = (
                "a hard safety boundary is already breached"
                if safety_breached
                else "a hard deadline or commitment is already breached"
            )
        elif (needs_more_info or uncertainty >= self.config.ask_uncertainty) and by_verb[Verb.OBSERVE]:
            verb, chosen = Verb.OBSERVE, self._best(by_verb[Verb.OBSERVE])
            rationale = "more information is available from a cheap check; look before asking anyone else"
        elif (uncertainty >= self.config.ask_uncertainty or confidence < self.config.min_confidence) and by_verb[Verb.ASK]:
            verb, chosen = Verb.ASK, self._best(by_verb[Verb.ASK])
            rationale = (
                f"uncertainty {uncertainty:.2f} is at or above {self.config.ask_uncertainty:.2f}"
                if uncertainty >= self.config.ask_uncertainty
                else f"confidence {confidence:.2f} is below the floor {self.config.min_confidence:.2f}"
            )
        elif verification_due and by_verb[Verb.VERIFY]:
            verb, chosen = Verb.VERIFY, self._best(by_verb[Verb.VERIFY])
            rationale = "a previous action has an unverified outcome"
        elif (
            urgency >= self.config.act_urgency
            and confidence >= self.config.act_confidence
            and by_verb[Verb.ACT]
        ):
            verb, chosen = Verb.ACT, self._best(by_verb[Verb.ACT])
            rationale = (
                f"urgency {urgency:.2f} and confidence {confidence:.2f} both clear the act thresholds "
                f"({self.config.act_urgency:.2f}, {self.config.act_confidence:.2f})"
            )
        elif urgency >= self.config.guide_urgency and by_verb[Verb.GUIDE]:
            verb, chosen = Verb.GUIDE, self._best(by_verb[Verb.GUIDE])
            rationale = f"urgency {urgency:.2f} clears the guide threshold {self.config.guide_urgency:.2f} but not act"
        elif by_verb[Verb.WAIT]:
            verb, chosen = Verb.WAIT, self._best(by_verb[Verb.WAIT])
            rationale = "no higher verb is admissible; keep observing"
        elif admitted:
            chosen = self._best(admitted)
            verb = chosen.verb if chosen else Verb.WAIT
            rationale = "higher verbs were unavailable; best admissible option selected"
        else:
            verb, rationale = Verb.WAIT, "no admissible option; keep observing"

        requires_approval = bool(
            chosen
            and verb == Verb.ACT
            and (
                chosen.requires_approval
                or chosen.destructive
                or self._approval_required(situation)
            )
        )
        if requires_approval:
            applied.append("approval:human-required")

        alternatives = self._alternatives(request.options, chosen, blocked, applied, verb)
        decision = Decision(
            verb=verb,
            confidence=confidence,
            reason_code="policy_rule",
            rationale=rationale,
            decision_id=decision_id,
            situation_id=situation.id,
            action_id=chosen.id if chosen else None,
            alternatives=alternatives,
            constraints_applied=tuple(dict.fromkeys(applied)),
            requires_approval=requires_approval,
            policy_version=self.version,
            created_at=created_at or iso(),
            trace_id=trace_id,
            score=chosen.utility if chosen else 0.0,
            attributes={
                "urgency": round(urgency, 4),
                "uncertainty": round(uncertainty, 4),
                "deadline_breached": deadline_breached,
                "safety_breached": safety_breached,
                "needs_more_info": needs_more_info,
            },
        )
        return decision

    # ------------------------------------------------------------- admission
    def _admit(
        self,
        situation: Situation,
        options: tuple[ActionOption, ...],
        applied: list[str],
        blocked: dict[str, str],
    ) -> list[ActionOption]:
        if self._safety_blocked(situation):
            applied.append("safety:blocked")
            for option in options:
                blocked[option.id] = "blocked by a hard safety constraint"
            return [item for item in options if item.verb == Verb.WAIT]

        admitted: list[ActionOption] = []
        for option in options:
            reason = self._violation(situation, option)
            if reason:
                blocked[option.id] = reason
                applied.append(reason)
            else:
                admitted.append(option)
        return admitted

    def _violation(self, situation: Situation, option: ActionOption) -> str | None:
        pairs = (
            ("latency", option.latency_ms, "ms"),
            ("cost", option.cost, ""),
            ("budget", option.cost, ""),
            ("risk", option.risk, ""),
            ("interruption", option.interrupt_cost, ""),
        )
        for kind, amount, unit in pairs:
            constraint = situation.constraint(kind)
            if constraint is None or not constraint.hard:
                continue
            limit = self._limit(kind, constraint.value, amount)
            if limit is None:
                continue
            if amount > limit:
                suffix = f" {unit}" if unit else ""
                return f"blocked by {kind}:{constraint.id} ({amount}{suffix} > {limit}{suffix})"
        return None

    @staticmethod
    def _limit(kind: str, value: Any, amount: float) -> float | None:
        if isinstance(value, dict):
            value = value.get("max", value.get("value"))
        if isinstance(value, bool) or value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        # A risk constraint expressed as "maximum risk" is already normalised.
        if kind == "interruption":
            return numeric if numeric <= 1.0 else numeric / 100.0
        return numeric

    def _safety_blocked(self, situation: Situation) -> bool:
        for constraint in situation.constraints:
            if constraint.kind == "safety" and constraint.hard and _truthy(constraint.value):
                return True
        return False

    def _approval_required(self, situation: Situation) -> bool:
        for constraint in situation.constraints:
            if constraint.kind == "approval" and _truthy(constraint.value):
                return True
        return False

    @staticmethod
    def _best(options: list[ActionOption]) -> ActionOption:
        return sorted(options, key=lambda item: (-item.utility, item.id))[0]

    # ----------------------------------------------------------- explanation
    def _alternatives(
        self,
        options: tuple[ActionOption, ...],
        chosen: ActionOption | None,
        blocked: dict[str, str],
        applied: list[str],
        chosen_verb: str,
    ) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for option in options:
            if chosen is not None and option.id == chosen.id:
                continue
            if option.id in blocked:
                reason = blocked[option.id]
            elif option.verb == chosen_verb:
                reason = "same verb, lower utility"
            else:
                reason = f"outranked by {chosen_verb}"
            rows.append(
                {
                    "action_id": option.id,
                    "verb": option.verb,
                    "name": option.name,
                    "utility": option.utility,
                    "rejected_because": reason,
                }
            )
        rows.sort(key=lambda item: (-float(item["utility"]), str(item["action_id"])))
        return tuple(rows[: self.config.max_alternatives])


def decide_action(request: ActionPolicyInput, *, config: ActionPolicyConfig | None = None, **kwargs: Any) -> Decision:
    """Functional shortcut for hosts that do not need a policy object."""
    return ActionPolicy(config).decide(request, **kwargs)



__all__ = [
    "ACTION_POLICY_VERSION",
    "ActionPolicy",
    "ActionPolicyConfig",
    "ActionPolicyInput",
    "decide_action",
]
