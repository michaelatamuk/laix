"""Internal row used while the commitment planner compares options."""

from __future__ import annotations

from dataclasses import dataclass

from ....decisions import ActionOption
from .commitment_score import CommitmentScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CommitmentScore
    feasible: bool
    blocker: str | None


__all__ = ["_Row"]
