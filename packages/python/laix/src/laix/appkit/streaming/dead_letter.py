"""One malformed source frame, kept for inspection."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...decision.support.time import iso


@dataclass(frozen=True, slots=True)
class DeadLetter:
    """One malformed source frame, kept for inspection."""

    raw: str
    error: str
    at: str = field(default_factory=iso)


__all__ = ["DeadLetter"]
