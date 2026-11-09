"""Internal row used while the commitment planner compares options."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ....domain.decisions import ActionOption
from .commitment_score import CommitmentScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CommitmentScore
    feasible: bool
    blocker: str | None
    blocked_by: tuple[dict[str, Any], ...] = ()


__all__ = ["_Row"]
