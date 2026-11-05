"""A small expected-utility engine with hard limits.

The engine is deliberately deterministic: it scores the options the app already
offered, rejects options outside a hard limit, and returns the same ``Plan``
shape as every other engine. A domain can replace it with an optimizer or a
learned model without changing the policy adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..decisions import ActionOption
from ..support.values import clamp
from .engine import DecisionProblem, Plan

RISK_ATTITUDES: tuple[str, ...] = ("neutral", "averse", "seeking")


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "required", "always", "blocked", "on"}
    return bool(value)


def _limit(kind: str, value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("max", value.get("value"))
    if isinstance(value, bool) or value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if kind == "interruption":
        return numeric if numeric <= 1.0 else numeric / 100.0
    return numeric


def _constraint_blocker(problem: DecisionProblem, option: ActionOption) -> str | None:
    """Return a reason when a hard situation constraint rejects the option."""
    situation = getattr(problem, "situation", None)
    if situation is None:
        return None
    amounts = {
        "risk": option.risk,
        "cost": option.cost,
        "budget": option.cost,
        "latency": option.latency_ms,
        "interruption": option.interrupt_cost,
    }
    for constraint in getattr(situation, "constraints", ()) or ():
        if not getattr(constraint, "hard", False):
            continue
        kind = str(getattr(constraint, "kind", ""))
        value = getattr(constraint, "value", None)
        if kind == "safety":
            if _truthy(value):
                return "safety"
            continue
        if kind not in amounts:
            continue
        limit = _limit(kind, value)
        if limit is not None and amounts[kind] > limit:
            identifier = getattr(constraint, "id", kind)
            return f"{kind}:{identifier}"
    return None


def _approval_required(problem: DecisionProblem) -> bool:
    situation = getattr(problem, "situation", None)
    if situation is None:
        return False
    for constraint in getattr(situation, "constraints", ()) or ():
        if getattr(constraint, "kind", "") == "approval" and _truthy(
            getattr(constraint, "value", False)
        ):
            return True
    return False


@dataclass(frozen=True, slots=True)
class UtilityWeights:
    """How much each cost subtracts from expected benefit."""

    benefit: float = 1.0
    cost: float = 0.25
    risk: float = 0.25
    interruption: float = 0.15
    latency: float = 0.0

    def __post_init__(self) -> None:
        for name in ("benefit", "cost", "risk", "interruption", "latency"):
            if getattr(self, name) < 0:
                raise ValueError(f"utility weight {name!r} must not be negative")


@dataclass(frozen=True, slots=True)
class UtilityModel:
    """Weights, risk attitude and the hard limits for one decision."""

    weights: UtilityWeights = field(default_factory=UtilityWeights)
    risk_attitude: str = "neutral"
    max_risk: float = 1.0
    max_cost: float | None = None
    max_latency_ms: float | None = None

    def __post_init__(self) -> None:
        if self.risk_attitude not in RISK_ATTITUDES:
            raise ValueError(f"unknown risk attitude: {self.risk_attitude}")
        if not 0.0 <= self.max_risk <= 1.0:
            raise ValueError("max_risk must be between zero and one")

    def feasible(self, option: ActionOption) -> bool:
        if option.risk > self.max_risk:
            return False
        if self.max_cost is not None and option.cost > self.max_cost:
            return False
        if self.max_latency_ms is not None and option.latency_ms > self.max_latency_ms:
            return False
        return True

    def score(self, option: ActionOption) -> float:
        weights = self.weights
        risk = option.risk
        if self.risk_attitude == "averse":
            risk = risk * (1.0 + risk)
        elif self.risk_attitude == "seeking":
            risk = risk * (1.0 - 0.5 * risk)
        return round(
            weights.benefit * option.expected_benefit
            - weights.cost * option.cost
            - weights.risk * risk
            - weights.interruption * option.interrupt_cost
            - weights.latency * option.latency_ms,
            6,
        )


class UtilityEngine:
    """Choose the feasible option with the highest expected utility."""

    name = "utility.v1"

    def __init__(self, model: UtilityModel | None = None) -> None:
        self.model = model or UtilityModel()

    def solve(self, problem: DecisionProblem) -> Plan:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._model_for(problem)
        feasible = [
            option
            for option in options
            if model.feasible(option) and _constraint_blocker(problem, option) is None
        ]
        if not feasible:
            return self._wait(
                "no_feasible_option",
                "every option is outside the hard limits",
            )

        scored = sorted(
            ((model.score(option), option) for option in feasible),
            key=lambda item: (-item[0], item[1].id),
        )
        best_score, best = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else None
        return Plan(
            verb=best.verb,
            confidence=self._confidence(best_score, second_score),
            reason_code="expected_utility",
            rationale=f"{best.id} has the highest expected utility {best_score:.3f}",
            action_id=best.id,
            requires_approval=(
                best.requires_approval or best.destructive or _approval_required(problem)
            ),
            reversible=best.reversible,
            score=best_score,
            alternatives=self._alternatives(problem, options, model, best),
            attributes={
                "utility": best_score,
                "risk_attitude": model.risk_attitude,
            },
        )

    def _model_for(self, problem: DecisionProblem) -> UtilityModel:
        attributes = problem.attributes
        overrides = {
            "max_risk": attributes.get("max_risk"),
            "max_cost": attributes.get("max_cost"),
            "max_latency_ms": attributes.get("max_latency_ms"),
        }
        present = {key: value for key, value in overrides.items() if value is not None}
        if not present:
            return self.model
        return UtilityModel(
            weights=self.model.weights,
            risk_attitude=str(attributes.get("risk_attitude", self.model.risk_attitude)),
            max_risk=float(present.get("max_risk", self.model.max_risk)),
            max_cost=float(present["max_cost"]) if "max_cost" in present else self.model.max_cost,
            max_latency_ms=(
                float(present["max_latency_ms"])
                if "max_latency_ms" in present
                else self.model.max_latency_ms
            ),
        )

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))

    @staticmethod
    def _alternatives(
        problem: DecisionProblem,
        options: list[ActionOption],
        model: UtilityModel,
        best: ActionOption,
    ) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for option in options:
            if option.id == best.id:
                continue
            blocker = _constraint_blocker(problem, option)
            if not model.feasible(option):
                reason = "outside the hard limits"
            elif blocker is not None:
                reason = f"blocked by {blocker}"
            else:
                reason = "lower expected utility"
            rows.append(
                {
                    "action_id": option.id,
                    "verb": option.verb,
                    "name": option.name,
                    "utility": model.score(option),
                    "rejected_because": reason,
                }
            )
        rows.sort(key=lambda item: (-float(item["utility"]), str(item["action_id"])))
        return tuple(rows)

    @staticmethod
    def _wait(reason_code: str, rationale: str) -> Plan:
        return Plan(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
        )


__all__ = ["RISK_ATTITUDES", "UtilityEngine", "UtilityModel", "UtilityWeights"]
