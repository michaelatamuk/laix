"""A reference to a commitment owned by this host or another party."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CommitmentRef:
    """A qualified reference to one commitment.

    ``owner`` identifies the party that made the promise. ``ledger`` is optional
    and lets one owner keep more than one ledger.
    """

    owner: str
    id: str
    ledger: str | None = None

    def __post_init__(self) -> None:
        if not self.owner:
            raise ValueError("commitment owner must not be empty")
        if not self.id:
            raise ValueError("commitment id must not be empty")

    @property
    def key(self) -> tuple[str, str, str]:
        """The stable lookup key used by :class:`CommitmentGraph`."""
        return (self.owner, self.ledger or "", self.id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "id": self.id,
            "ledger": self.ledger,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CommitmentRef":
        return cls(
            owner=str(payload["owner"]),
            id=str(payload["id"]),
            ledger=payload.get("ledger"),
        )


__all__ = ["CommitmentRef"]
