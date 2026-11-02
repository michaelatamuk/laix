"""One request, whichever generic policy the app needs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .action_option import ActionOption
from .situation import Situation


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    """One request, whichever generic policy the app needs.

    Provide ``situation`` and ``options`` for action selection, or ``signals``
    and ``context`` for attention allocation. Both paths return ``Decision``.
    """

    subject: str
    at: str
    signals: tuple[Any, ...] = ()
    context: Any = None
    situation: Situation | None = None
    options: tuple[ActionOption, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    confidence_source: str = ""
    calibrated: bool = False


__all__ = ["DecisionRequest"]
