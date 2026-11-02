"""Preference elicitation: ask the question that best reduces uncertainty."""

from __future__ import annotations

from typing import Any

from ...decisions import Decision, Intent
from .._support import decision, number, value


class PreferenceElicitationPolicy:
    name = "preference-elicitation.v1"
    version = "0.8.0"

    def decide(self, request: Any) -> list[Decision]:
        uncertainty = number(request, "uncertainty", 0.5)
        threshold = number(request, "uncertainty_threshold", 0.2)
        questions = tuple(value(request, "questions", ()) or ())

        if uncertainty <= threshold:
            return [
                decision(
                    policy=self.name,
                    verb="act",
                    reason_code="preference_known",
                    rationale="uncertainty is low enough to choose without another question",
                    confidence=1.0 - uncertainty,
                )
            ]
        if not questions:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="no_question",
                    rationale="no useful question is available",
                    confidence=0.5,
                )
            ]

        best = max(
            questions,
            key=lambda item: float(item.get("information_gain", 0))
            / max(float(item.get("cost", 0)), 0.001),
        )
        gain = float(best.get("information_gain", 0))
        return [
            decision(
                policy=self.name,
                verb="ask",
                reason_code="ask_preference",
                rationale=f"ask {best.get('id', '?')} to reduce preference uncertainty",
                confidence=min(0.95, 0.5 + gain),
                intent=Intent("ask_question", {"id": str(best.get("id", ""))}),
                score=round(gain, 6),
                action_id=str(best.get("id", "")),
            )
        ]


__all__ = ["PreferenceElicitationPolicy"]
