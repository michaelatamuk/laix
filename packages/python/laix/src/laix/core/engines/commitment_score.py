"""The utility and commitment parts of one option's score."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommitmentScore:
    """The utility and commitment parts of one option's score."""

    utility: float
    commitment: float
    total: float
    fulfilled: tuple[str, ...] = ()
    violated: tuple[str, ...] = ()
    created: tuple[str, ...] = ()
    due_fulfilled: tuple[str, ...] = ()
    due_violated: tuple[str, ...] = ()
    blocked_fulfilled: tuple[str, ...] = ()
    blocked: str | None = None


__all__ = ["CommitmentScore"]
