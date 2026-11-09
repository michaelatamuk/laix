"""Active perception: choose the next look when uncertainty is high."""

from __future__ import annotations

from typing import Any

from ......domain.decisions import Decision, Intent
from ......support.verbs import Verb
from ._helpers import decision, number, value


class ActivePerceptionPolicy:
    name = "active-perception.v1"
    version = "0.8.0"

    def decide(self, request: Any) -> list[Decision]:
        uncertainty = number(request, "uncertainty", 0.5)
        minimum = number(request, "min_information_gain", 0.2)
        budget = number(request, "budget", float("inf"))
        observations = tuple(value(request, "observations", ()) or ())

        if uncertainty < minimum:
            return [
                decision(
                    policy=self.name,
                    verb=Verb.WAIT,
                    reason_code="uncertainty_low",
                    rationale="uncertainty is low enough to decide without another look",
                    confidence=1.0 - uncertainty,
                )
            ]
        if not observations:
            return [
                decision(
                    policy=self.name,
                    verb=Verb.WAIT,
                    reason_code="no_observation",
                    rationale="no observation is available",
                    confidence=0.4,
                )
            ]

        best = max(
            observations,
            key=lambda item: float(item.get("information_gain", 0)) * uncertainty
            / max(float(item.get("cost", 0)), 0.001),
        )
        gain = float(best.get("information_gain", 0)) * uncertainty
        cost = float(best.get("cost", 0))
        if gain < minimum or cost > budget:
            return [
                decision(
                    policy=self.name,
                    verb=Verb.WAIT,
                    reason_code="observation_not_worth_it",
                    rationale="the available observation costs more than it is expected to resolve",
                    confidence=0.5,
                )
            ]
        return [
            decision(
                policy=self.name,
                verb=Verb.OBSERVE,
                reason_code="observe_for_information",
                rationale=f"take observation {best.get('id', '?')} to reduce uncertainty",
                confidence=min(0.95, 0.5 + gain),
                intent=Intent("observe", {"id": str(best.get("id", ""))}),
                score=round(gain, 6),
                action_id=str(best.get("id", "")),
            )
        ]


__all__ = ["ActivePerceptionPolicy"]
