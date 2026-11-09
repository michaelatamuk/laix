"""Severity ordering for attention signals."""

from __future__ import annotations

SEVERITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

def rank(severity: str) -> int:
    """Lower is more severe."""
    return SEVERITY_RANK.get(severity, 9)


__all__ = ["SEVERITY_RANK", "rank"]
