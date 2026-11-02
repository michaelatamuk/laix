"""Severity ordering for attention signals."""

from __future__ import annotations

SEVERITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

__all__ = ["SEVERITY_RANK"]
