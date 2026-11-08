"""Resource policy: which perception or model call is worth making.

Two rules, both deterministic:

* cheap detectors run continuously;
* a deep call is admitted only when its expected information gain, weighted by
  the current uncertainty, clears a threshold and the budget still allows it.

The policy reports what it skipped and why, so "deep calls saved" is measured
rather than claimed.
"""

from __future__ import annotations

from typing import Any, Iterable

from ....support.values import clamp
from .budget import Budget
from .plan import ResourcePlan
from .sensing_option import SensingOption


class ResourceScheduler:
    def __init__(self, *, min_information_gain: float = 0.35) -> None:
        self.min_information_gain = min_information_gain

    def schedule(
        self,
        options: Iterable[SensingOption],
        *,
        budget: Budget | None = None,
        uncertainty: float = 0.5,
    ) -> ResourcePlan:
        budget = budget or Budget()
        uncertainty = clamp(uncertainty)
        allowed: list[str] = []
        skipped: list[dict[str, Any]] = []
        deep_calls = 0
        cost = 0.0

        for option in options:
            if option.tier == "cheap":
                allowed.append(option.name)
                cost += option.cost
                continue
            reason = None
            gain = option.information_gain * max(uncertainty, 0.05)
            if deep_calls >= budget.max_deep_calls:
                reason = "deep-call budget exhausted"
            elif cost + option.cost > budget.max_cost:
                reason = "cost budget exhausted"
            elif option.latency_ms > budget.max_latency_ms:
                reason = "latency budget exceeded"
            elif gain < self.min_information_gain:
                reason = f"information gain {gain:.2f} below threshold {self.min_information_gain:.2f}"
            if reason:
                skipped.append({"name": option.name, "reason": reason, "gain": round(gain, 3)})
                continue
            allowed.append(option.name)
            deep_calls += 1
            cost += option.cost

        return ResourcePlan(
            allowed=tuple(allowed),
            skipped=tuple(skipped),
            deep_calls=deep_calls,
            cost=cost,
            reason="cheap continuous; deep calls admitted by gain, uncertainty and budget",
            attributes={"uncertainty": round(uncertainty, 3), "threshold": self.min_information_gain},
        )

    @staticmethod
    def should_escalate(confidence: float, *, required: float = 0.75) -> bool:
        """The cheap model is not sure enough; ask for the expensive one."""
        return clamp(confidence) < clamp(required)


__all__ = ["ResourceScheduler"]
