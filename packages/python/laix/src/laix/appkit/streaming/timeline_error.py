"""An error raised when a decision breaks timeline semantics."""

from __future__ import annotations


class TimelineError(ValueError):
    """A decision breaks the timeline semantics."""


__all__ = ["TimelineError"]
