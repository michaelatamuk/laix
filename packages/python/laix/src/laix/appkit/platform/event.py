"""One platform event streamed back for a trace."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PlatformEvent:
    trace_id: str
    kind: str
    at: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


__all__ = ["PlatformEvent"]
