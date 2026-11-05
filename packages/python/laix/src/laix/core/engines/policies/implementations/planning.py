"""A policy that turns open commitments into the next task move."""

from __future__ import annotations

from typing import Any

from ....decisions import Decision
from ....planning import CommitmentLedger
from ....support.time import parse_iso, utcnow
from ....support.verbs import Verb


class PlanningPolicy:
    """Act on a due commitment, ask when blocked, wait otherwise."""

    name = "planning.v1"

    def __init__(self, ledger: CommitmentLedger) -> None:
        self.ledger = ledger
        self.version = self.name

    def decide(self, request: Any) -> list[Decision]:
        now = parse_iso(getattr(request, "at", None)) or utcnow()
        commitment = self.ledger.next(now)
        if commitment is None:
            return [self._decision(Verb.WAIT, "no_commitment", "there is no open commitment", 0.8)]
        if self.ledger.blocked(commitment):
            return [
                self._decision(
                    Verb.ASK,
                    "blocked_commitment",
                    f"{commitment.id} waits on another commitment",
                    0.7,
                    action_id=commitment.id,
                )
            ]
        if commitment.is_due(now):
            return [
                self._decision(
                    Verb.ACT,
                    "due_commitment",
                    f"{commitment.id} is due",
                    0.9,
                    action_id=commitment.id,
                )
            ]
        return [
            self._decision(
                Verb.WAIT,
                "not_due",
                f"{commitment.id} is not due yet",
                0.8,
                action_id=commitment.id,
            )
        ]

    def _decision(
        self,
        verb: str,
        reason_code: str,
        rationale: str,
        confidence: float,
        *,
        action_id: str | None = None,
    ) -> Decision:
        return Decision(
            verb=verb,
            confidence=confidence,
            reason_code=reason_code,
            rationale=rationale,
            action_id=action_id,
            policy_version=self.name,
        )


__all__ = ["PlanningPolicy"]
