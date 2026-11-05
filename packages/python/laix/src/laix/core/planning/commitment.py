"""Commitments: the small planning state a task can carry between decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..support.time import parse_iso

COMMITMENT_STATUSES = ("open", "done", "cancelled")
_NEVER = datetime.max.replace(tzinfo=timezone.utc)


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


class CommitmentLedger:
    """An in-memory set of commitments for one task."""

    def __init__(self, commitments: tuple[Commitment, ...] = ()) -> None:
        self._items: dict[str, Commitment] = {item.id: item for item in commitments}

    def add(self, commitment: Commitment) -> Commitment:
        self._items[commitment.id] = commitment
        return commitment

    def get(self, commitment_id: str) -> Commitment:
        return self._items[commitment_id]

    def complete(self, commitment_id: str) -> Commitment:
        return self._replace(commitment_id, status="done")

    def cancel(self, commitment_id: str) -> Commitment:
        return self._replace(commitment_id, status="cancelled")

    def open(self) -> tuple[Commitment, ...]:
        return tuple(item for item in self._items.values() if item.status == "open")

    def due(self, now: datetime) -> tuple[Commitment, ...]:
        return tuple(item for item in self.open() if item.is_due(now))

    def next(self, now: datetime | None = None) -> Commitment | None:
        open_items = self.open()
        if not open_items:
            return None
        return self._first(open_items)

    def next_actionable(self, now: datetime | None = None) -> Commitment | None:
        """Return the earliest open commitment whose dependencies are complete."""
        open_items = [item for item in self.open() if not self.blocked(item)]
        if not open_items:
            return None
        return self._first(open_items)

    def blocked_open(self) -> tuple[Commitment, ...]:
        """Return open commitments that still wait on another commitment."""
        return tuple(item for item in self.open() if self.blocked(item))

    @staticmethod
    def _first(items: list[Commitment]) -> Commitment:
        return sorted(
            items,
            key=lambda item: (parse_iso(item.due) or _NEVER, -item.priority, item.id),
        )[0]

    def blocked(self, commitment: Commitment) -> bool:
        for dependency in commitment.depends_on:
            item = self._items.get(dependency)
            if item is None or item.status != "done":
                return True
        return False

    def _replace(self, commitment_id: str, *, status: str) -> Commitment:
        item = self.get(commitment_id)
        updated = Commitment(
            id=item.id,
            subject=item.subject,
            due=item.due,
            status=status,
            depends_on=item.depends_on,
            priority=item.priority,
            payload=dict(item.payload),
        )
        self._items[commitment_id] = updated
        return updated

    def to_dict(self) -> dict[str, Any]:
        return {"commitments": [item.to_dict() for item in self._items.values()]}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CommitmentLedger":
        return cls(
            tuple(
                Commitment.from_dict(item)
                for item in payload.get("commitments", ())
            )
        )


__all__ = ["COMMITMENT_STATUSES", "Commitment", "CommitmentLedger"]
