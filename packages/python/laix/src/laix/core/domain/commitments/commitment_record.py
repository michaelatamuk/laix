"""One promised step, with its due time and dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ...support.time import parse_iso

COMMITMENT_STATUSES = ("open", "done", "cancelled")


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

    def __post_init__(self) -> None:
        if self.status not in COMMITMENT_STATUSES:
            raise ValueError(f"unknown commitment status: {self.status}")

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
        )


__all__ = ["COMMITMENT_STATUSES", "Commitment"]
