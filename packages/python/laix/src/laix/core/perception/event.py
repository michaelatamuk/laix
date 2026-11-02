"""One input to the loop: what happened, when and where."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PerceptionEvent:
    """One input to the loop: what happened, when and where."""

    subject: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)


__all__ = ["PerceptionEvent"]
