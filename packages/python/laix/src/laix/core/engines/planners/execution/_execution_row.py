"""Internal row used while the execution planner compares options."""

from __future__ import annotations

from dataclasses import dataclass

from ....decisions import ActionOption
from .execution_score import ExecutionScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: ExecutionScore
    feasible: bool
    blocker: str | None


__all__ = ["_Row"]
