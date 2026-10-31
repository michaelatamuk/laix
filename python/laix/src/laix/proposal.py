"""A small, storage-free proposal and approval record.

A proposal is the app-facing form of an action that needs a person: what is
proposed, by whom, what it will change, and whether it was approved, rejected,
applied or undone. The app owns the store; this module owns the lifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

PROPOSAL_STATUSES: tuple[str, ...] = ("pending", "approved", "rejected", "applied", "undone")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class Proposal:
    id: str
    title: str
    summary: str
    decision_id: str = ""
    action_id: str | None = None
    status: str = "pending"
    created_at: str = field(default_factory=_now)
    created_by: str = "agent"
    approved_by: str | None = None
    approved_at: str | None = None
    applied_at: str | None = None
    undo_hint: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in PROPOSAL_STATUSES:
            raise ValueError(f"unknown proposal status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


def approve(proposal: Proposal, *, by: str, at: str | None = None) -> Proposal:
    if proposal.status != "pending":
        raise ValueError(f"cannot approve a {proposal.status} proposal")
    moment = at or _now()
    return replace(
        proposal,
        status="approved",
        approved_by=by,
        approved_at=moment,
    )


def reject(proposal: Proposal, *, by: str, at: str | None = None) -> Proposal:
    if proposal.status != "pending":
        raise ValueError(f"cannot reject a {proposal.status} proposal")
    return replace(
        proposal,
        status="rejected",
        approved_by=by,
        approved_at=at or _now(),
    )


def apply(proposal: Proposal, *, at: str | None = None) -> Proposal:
    if proposal.status != "approved":
        raise ValueError(f"cannot apply a {proposal.status} proposal")
    return replace(proposal, status="applied", applied_at=at or _now())


def undo(proposal: Proposal, *, at: str | None = None) -> Proposal:
    if proposal.status != "applied":
        raise ValueError(f"cannot undo a {proposal.status} proposal")
    return replace(proposal, status="undone", applied_at=at or _now())


__all__ = ["PROPOSAL_STATUSES", "Proposal", "approve", "reject", "apply", "undo"]
