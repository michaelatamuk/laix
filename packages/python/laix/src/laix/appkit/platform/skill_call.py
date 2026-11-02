"""One named skill call the app asks the platform to run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillCall:
    capability: str
    args: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""


__all__ = ["SkillCall"]
