"""Causal attribution for observed outcomes.

This is a small, explicit estimator: compare one treatment arm with one control
arm by difference in means, or by inverse propensity weighting when every
observation carries a propensity strictly between zero and one. It is not a
causal discovery engine; it makes the assumption visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class CausalObservation:
    """One decision, its arm and the measured outcome."""

    decision_id: str
    arm: str
    outcome: float
    propensity: float | None = None
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CausalEffect:
    """The estimated effect of one arm against another."""

    treatment: str
    control: str
    estimate: float
    treated: int
    control_size: int
    method: str


def _weighted_mean(
    items: list[CausalObservation],
    weight: Callable[[float], float],
) -> float:
    total = 0.0
    for item in items:
        if item.propensity is None:
            raise ValueError("propensity is required for weighting")
        total += item.outcome * weight(item.propensity)
    return total / len(items)


class CausalLedger:
    """Collect observations and estimate one treatment effect."""

    def __init__(self) -> None:
        self.records: list[CausalObservation] = []

    def add(
        self,
        decision_id: str,
        *,
        arm: str,
        outcome: float,
        propensity: float | None = None,
        context: dict[str, Any] | None = None,
    ) -> CausalObservation:
        if propensity is not None and not 0.0 <= propensity <= 1.0:
            raise ValueError("propensity must be between zero and one")
        observation = CausalObservation(
            decision_id=decision_id,
            arm=arm,
            outcome=float(outcome),
            propensity=None if propensity is None else float(propensity),
            context=dict(context or {}),
        )
        self.records.append(observation)
        return observation

    def effect(self, treatment: str, control: str) -> CausalEffect:
        treated = [item for item in self.records if item.arm == treatment]
        controlled = [item for item in self.records if item.arm == control]
        if not treated or not controlled:
            raise ValueError("both arms need at least one observation")

        weighted = all(
            item.propensity is not None and 0.0 < item.propensity < 1.0
            for item in treated + controlled
        )
        if weighted:
            treated_mean = _weighted_mean(treated, lambda value: 1.0 / value)
            control_mean = _weighted_mean(controlled, lambda value: 1.0 / (1.0 - value))
            method = "inverse-propensity"
        else:
            treated_mean = sum(item.outcome for item in treated) / len(treated)
            control_mean = sum(item.outcome for item in controlled) / len(controlled)
            method = "difference-in-means"

        return CausalEffect(
            treatment=treatment,
            control=control,
            estimate=round(treated_mean - control_mean, 6),
            treated=len(treated),
            control_size=len(controlled),
            method=method,
        )


__all__ = ["CausalEffect", "CausalLedger", "CausalObservation"]
