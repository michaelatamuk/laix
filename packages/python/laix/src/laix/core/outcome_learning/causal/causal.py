"""Causal attribution for observed outcomes.

This is a small, explicit estimator: compare one treatment arm with one control
arm by difference in means, or by inverse propensity weighting when every
observation carries a propensity strictly between zero and one. It is not a
causal discovery engine; it makes the assumption visible.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Iterable, Mapping

from .causal_effect import CausalEffect
from .causal_observation import CausalObservation
from ..record import Outcome


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


def _variance(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


def _weighted_variance(
    items: list[CausalObservation],
    weight: Callable[[float], float],
    mean: float,
) -> float:
    if len(items) < 2:
        return 0.0
    total = 0.0
    for item in items:
        if item.propensity is None:
            raise ValueError("propensity is required for weighting")
        total += (weight(item.propensity) ** 2) * ((item.outcome - mean) ** 2)
    return total / (len(items) ** 2)


def _interval(estimate: float, standard_error: float) -> tuple[float, float]:
    return (
        round(estimate - 1.96 * standard_error, 6),
        round(estimate + 1.96 * standard_error, 6),
    )


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

    def add_outcome(
        self,
        outcome: Outcome,
        *,
        arm: str,
        propensity: float | None = None,
        context: dict[str, Any] | None = None,
        signed: bool = True,
    ) -> CausalObservation:
        """Add one measured outcome to an arm.

        The measured ``delta`` is oriented so a positive value always means
        improvement. For a ``lower-better`` metric, the sign is flipped.
        """
        value = float(outcome.delta)
        if signed and outcome.direction == "lower-better":
            value = -value
        return self.add(
            outcome.decision_id,
            arm=arm,
            outcome=value,
            propensity=propensity,
            context=context,
        )

    @classmethod
    def from_outcomes(
        cls,
        outcomes: Iterable[Outcome],
        arms: Mapping[str, str],
        *,
        default_arm: str | None = None,
        propensities: Mapping[str, float] | None = None,
        contexts: Mapping[str, Mapping[str, Any]] | None = None,
        signed: bool = True,
    ) -> "CausalLedger":
        """Build a ledger from outcome records and a decision-to-arm map."""
        ledger = cls()
        for outcome in outcomes:
            arm = arms.get(outcome.decision_id, default_arm)
            if arm is None:
                continue
            ledger.add_outcome(
                outcome,
                arm=arm,
                propensity=(propensities or {}).get(outcome.decision_id),
                context=dict((contexts or {}).get(outcome.decision_id, {})),
                signed=signed,
            )
        return ledger

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
            treated_variance = _weighted_variance(
                treated, lambda value: 1.0 / value, treated_mean
            )
            control_variance = _weighted_variance(
                controlled, lambda value: 1.0 / (1.0 - value), control_mean
            )
            method = "inverse-propensity"
        else:
            treated_mean = sum(item.outcome for item in treated) / len(treated)
            control_mean = sum(item.outcome for item in controlled) / len(controlled)
            treated_variance = _variance(
                [item.outcome for item in treated], treated_mean
            ) / len(treated)
            control_variance = _variance(
                [item.outcome for item in controlled], control_mean
            ) / len(controlled)
            method = "difference-in-means"

        estimate = round(treated_mean - control_mean, 6)
        standard_error = round(math.sqrt(treated_variance + control_variance), 6)
        low, high = _interval(estimate, standard_error)
        return CausalEffect(
            treatment=treatment,
            control=control,
            estimate=estimate,
            treated=len(treated),
            control_size=len(controlled),
            method=method,
            standard_error=standard_error,
            ci_low=low,
            ci_high=high,
        )

    def effect_by_context(
        self,
        treatment: str,
        control: str,
        *,
        key: str = "stratum",
    ) -> dict[str, CausalEffect]:
        """Estimate one effect per context value, skipping incomplete strata."""
        buckets: dict[str, list[CausalObservation]] = {}
        for item in self.records:
            stratum = str(item.context.get(key, "all"))
            buckets.setdefault(stratum, []).append(item)
        effects: dict[str, CausalEffect] = {}
        for stratum, records in sorted(buckets.items()):
            arms = {item.arm for item in records}
            if treatment not in arms or control not in arms:
                continue
            ledger = CausalLedger()
            ledger.records = records
            effects[stratum] = ledger.effect(treatment, control)
        return effects


__all__ = ["CausalEffect", "CausalLedger", "CausalObservation"]
