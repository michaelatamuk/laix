"""The four labels an outcome can carry."""

from __future__ import annotations

from enum import StrEnum


class OutcomeLabel(StrEnum):
    """The four labels an outcome can carry."""

    HELPED = "helped"
    NEUTRAL = "neutral"
    HURT = "hurt"
    UNKNOWN = "unknown"


__all__ = ["OutcomeLabel"]
