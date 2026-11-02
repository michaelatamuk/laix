"""Whether a decision record can still be undone."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Undo:
    available: bool = False
    how: str | None = None
    at: str | None = None


__all__ = ["Undo"]
