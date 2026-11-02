"""What the user has already said about this signal."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Feedback:
    """What the user has already said about this signal.

    ``snoozed`` needs ``until``; ``accepted`` never suppresses; ``wrong`` and
    ``assigned`` and ``dismissed`` do.
    """

    state: str
    at: str | None = None
    until: str | None = None
    note: str | None = None


__all__ = ["Feedback"]
