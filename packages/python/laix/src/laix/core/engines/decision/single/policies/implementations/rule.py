"""One condition and the decision it produces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ......decisions import Intent


@dataclass(frozen=True, slots=True)
class Rule:
    """One condition and the decision it produces."""

    when: dict[str, Any]
    verb: str
    reason_code: str
    rationale: str = ""
    confidence: float = 0.8
    action_id: str | None = None
    requires_approval: bool = False
    intent: Intent | None = None


__all__ = ["Rule"]
