"""Internal row used while the attention planner compares options."""

from __future__ import annotations

from dataclasses import dataclass

from ..decisions import ActionOption
from .attention_score import AttentionScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: AttentionScore
    feasible: bool
    blocker: str | None


__all__ = ["_Row"]
