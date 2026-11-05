"""Internal row used while the live planner compares options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..decisions import ActionOption
from .live_score import LiveScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: LiveScore
    feasible: bool
    blocker: str | None
    commitment: Any
    execution: Any
    attention: Any


__all__ = ["_Row"]
