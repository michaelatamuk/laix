"""A policy that turns open commitments into the next task move."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ...domain.decisions import Decision
from ...domain.commitments import CommitmentGraph, CommitmentLedger
from ...support.time import parse_iso, utcnow
from ...support.verbs import Verb


class PlanningPolicy:
    """Act on a due commitment, ask when blocked, wait otherwise."""

    name = "planning.v1"

    def __init__(
        self,
        ledger: CommitmentLedger,
        *,
        commitment_graph: CommitmentGraph | None = None,
        require_verified: bool = False,
        max_verification_age: timedelta | None = None,
    ) -> None:
        self.ledger = ledger
        self.commitment_graph = commitment_graph
        self.require_verified = require_verified
        self.max_verification_age = max_verification_age
        self.version = self.name

    def decide(self, request: Any) -> list[Decision]:
        now = parse_iso(getattr(request, "at", None)) or utcnow()
        graph = self.commitment_graph
        if graph is not None:
            commitment = graph.next_actionable(
                now,
                require_verified=self.require_verified,
                max_verification_age=self.max_verification_age,
            )
            blocked = graph.blocked_open(
                require_verified=self.require_verified,
                now=now,
                max_verification_age=self.max_verification_age,
            )
        else:
            commitment = self.ledger.next_actionable(now)
            blocked = self.ledger.blocked_open()
        if commitment is None:
            if blocked:
                first = blocked[0]
                return [
                    self._decision(
                        Verb.ASK,
                        "blocked_commitment",
                        f"{first.id} waits on another commitment",
                        0.7,
                        action_id=first.id,
                        attributes={"commitment_id": first.id},
                    )
                ]
            return [self._decision(Verb.WAIT, "no_commitment", "there is no open commitment", 0.8)]
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
        attributes: dict[str, Any] | None = None,
    ) -> Decision:
        return Decision(
            verb=verb,
            confidence=confidence,
            reason_code=reason_code,
            rationale=rationale,
            action_id=action_id,
            attributes=dict(attributes or {}),
            policy_version=self.name,
        )


__all__ = ["PlanningPolicy"]
