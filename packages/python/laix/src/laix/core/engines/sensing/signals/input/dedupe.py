"""Deduplication key for one signal and one day."""

from __future__ import annotations

from datetime import datetime

from .signal import Signal


def dedupe_key(signal: Signal, now: datetime) -> str:
    """One interruption per signal per day, by default."""
    return f"{signal.id}:{now.date().isoformat()}"


__all__ = ["dedupe_key"]
