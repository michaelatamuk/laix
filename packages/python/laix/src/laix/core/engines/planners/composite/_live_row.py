"""Internal row used while the live planner compares options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ....decisions import ActionOption
from .composite_score import CompositeScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CompositeScore
    feasible: bool
    blocker: str | None
    commitment: Any
    execution: Any
    human_attention: Any


__all__ = ["_Row"]
