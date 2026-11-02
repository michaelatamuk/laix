"""Proof that an action was executed, refused, cancelled or undone."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..serialize import to_primitive
from ..time import iso
from ..version import SCHEMA_VERSION

RECEIPT_STATUSES: tuple[str, ...] = (
    "pending",
    "approved",
    "executed",
    "refused",
    "cancelled",
    "failed",
    "undone",
)


@dataclass(frozen=True, slots=True)
class Receipt:
    """Proof that an action was executed, refused, cancelled or undone."""

    id: str
    decision_id: str
    action_name: str
    status: str
    actor: str
    at: str = field(default_factory=iso)
    detail: dict[str, Any] = field(default_factory=dict)
    previous_state: dict[str, Any] | None = None
    error: str | None = None
    approved_by: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.status not in RECEIPT_STATUSES:
            raise ValueError(f"unknown receipt status: {self.status}")

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["RECEIPT_STATUSES", "Receipt"]
