"""One promised step, with its due time, owner and dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ...support.time import parse_iso
from .commitment_ref import CommitmentRef

COMMITMENT_STATUSES = ("open", "done", "cancelled")
COMMITMENT_SOURCES = ("local", "reported", "verified")


@dataclass(frozen=True, slots=True)
class Commitment:
    """One promised step, with its due time and dependencies."""

    id: str
    subject: str
    due: str | None = None
    status: str = "open"
    depends_on: tuple[str, ...] = ()
    priority: float = 0.5
    payload: dict[str, Any] = field(default_factory=dict)
    owner: str = "local"
    ledger: str | None = None
    source: str = "local"
    verified_at: str | None = None
    external_depends_on: tuple[CommitmentRef, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in COMMITMENT_STATUSES:
            raise ValueError(f"unknown commitment status: {self.status}")
        if self.source not in COMMITMENT_SOURCES:
            raise ValueError(f"unknown commitment source: {self.source}")
        if not self.owner:
            raise ValueError("commitment owner must not be empty")

    @property
    def key(self) -> tuple[str, str, str]:
        """The stable lookup key used by :class:`CommitmentGraph`."""
        return (self.owner, self.ledger or "", self.id)

    @property
    def trusted(self) -> bool:
        """Local and verified commitments may be used as decision evidence."""
        return self.source in {"local", "verified"}

    def is_due(self, now: datetime) -> bool:
        due = parse_iso(self.due)
        return due is not None and due <= now

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject": self.subject,
            "due": self.due,
            "status": self.status,
            "depends_on": list(self.depends_on),
            "priority": self.priority,
            "payload": dict(self.payload),
            "owner": self.owner,
            "ledger": self.ledger,
            "source": self.source,
            "verified_at": self.verified_at,
            "external_depends_on": [item.to_dict() for item in self.external_depends_on],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Commitment":
        return cls(
            id=str(payload["id"]),
            subject=str(payload.get("subject", "")),
            due=payload.get("due"),
            status=str(payload.get("status", "open")),
            depends_on=tuple(payload.get("depends_on", ())),
            priority=float(payload.get("priority", 0.5)),
            payload=dict(payload.get("payload", {})),
            owner=str(payload.get("owner", "local")),
            ledger=payload.get("ledger"),
            source=str(payload.get("source", "local")),
            verified_at=payload.get("verified_at"),
            external_depends_on=tuple(
                item
                if isinstance(item, CommitmentRef)
                else CommitmentRef.from_dict(dict(item))
                for item in payload.get("external_depends_on", ())
            ),
        )


__all__ = ["COMMITMENT_SOURCES", "COMMITMENT_STATUSES", "Commitment"]
