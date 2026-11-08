"""Weights, risk attitude and the hard limits for one decision."""

from __future__ import annotations

from dataclasses import dataclass, field

from ......decisions import ActionOption
from .utility_weights import UtilityWeights

RISK_ATTITUDES: tuple[str, ...] = ("neutral", "averse", "seeking")


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


__all__ = ["RISK_ATTITUDES", "UtilityModel"]
