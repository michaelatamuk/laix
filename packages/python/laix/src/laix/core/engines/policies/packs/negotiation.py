"""Negotiation: accept, counter or walk from a simple offer."""

from __future__ import annotations

from typing import Any

from ....decisions import Decision, Intent
from .._support import decision, number, value


class NegotiationPolicy:
    name = "negotiation.v1"
    version = "0.8.0"

    def decide(self, request: Any) -> list[Decision]:
        offer = number(request, "offer", 0.0)
        reservation = number(request, "reservation", 0.0)
        target = number(request, "target", reservation)
        round_number = int(number(request, "round", 1))
        max_rounds = int(number(request, "max_rounds", 5))

        if offer >= reservation:
            return [
                decision(
                    policy=self.name,
                    verb="act",
                    reason_code="accept_offer",
                    rationale=f"the offer {offer:.2f} meets the reservation {reservation:.2f}",
                    confidence=0.95,
                    intent=Intent("accept_offer", {"amount": offer}),
                    action_id="accept_offer",
                )
            ]
        if round_number >= max_rounds:
            return [
                decision(
                    policy=self.name,
                    verb="escalate",
                    reason_code="round_limit",
                    rationale="the round limit is reached without an acceptable offer",
                    confidence=0.8,
                )
            ]
        counter = max(reservation, (offer + target) / 2.0)
        return [
            decision(
                policy=self.name,
                verb="act",
                reason_code="counter_offer",
                rationale=f"counter at {counter:.2f}, between the offer {offer:.2f} and target {target:.2f}",
                confidence=0.7,
                intent=Intent("counter_offer", {"amount": counter}),
                action_id="counter_offer",
            )
        ]


__all__ = ["NegotiationPolicy"]
