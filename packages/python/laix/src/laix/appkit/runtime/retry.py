"""Retry policy for one execution attempt chain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How many times to retry a failed handler, and how long to wait."""

    attempts: int = 1
    backoff_seconds: float = 0.0
    max_backoff_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("attempts must be at least 1")
        if self.backoff_seconds < 0 or self.max_backoff_seconds < 0:
            raise ValueError("backoff must not be negative")

    def delay(self, attempt: int) -> float:
        """Exponential backoff after a failed attempt, capped."""
        if self.backoff_seconds <= 0:
            return 0.0
        return min(
            self.backoff_seconds * (2 ** (attempt - 1)),
            self.max_backoff_seconds,
        )


__all__ = ["RetryPolicy"]
