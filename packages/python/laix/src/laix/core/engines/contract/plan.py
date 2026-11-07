"""The planner's answer, before it becomes a ``Decision``."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...decisions import Intent


@dataclass(frozen=True, slots=True)
class Plan:
    """The planner's answer, before it becomes a ``Decision``."""

    verb: str
    confidence: float
    reason_code: str
    rationale: str
    action_id: str | None = None
    intent: Intent | None = None
    requires_approval: bool = False
    reversible: bool = False
    undo_hint: str | None = None
    score: float | None = None
    alternatives: tuple[dict[str, Any], ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


__all__ = ["Plan"]
