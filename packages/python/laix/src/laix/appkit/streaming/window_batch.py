"""One closed tumbling window."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ...decision.domain.decisions import DecisionRequest


@dataclass(frozen=True, slots=True)
class WindowBatch:
    """One closed tumbling window."""

    start: datetime
    end: datetime
    events: tuple[DecisionRequest, ...]


__all__ = ["WindowBatch"]
