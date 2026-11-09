"""Internal row used while the CA-VOD planner compares options."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ......domain.decisions import ActionOption
from .ca_vod_score import CAVODScore


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CAVODScore
    feasible: bool
    blocker: str | None
    commitment: Any = field(repr=False)
    execution: Any = field(repr=False)
    human_attention: Any = field(repr=False)


__all__ = ["_Row"]
