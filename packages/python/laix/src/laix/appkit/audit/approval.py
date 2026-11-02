"""The approval state carried by a decision record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Approval:
    required: bool
    state: str = "pending"
    by: str | None = None
    at: str | None = None
    note: str | None = None


__all__ = ["Approval"]
