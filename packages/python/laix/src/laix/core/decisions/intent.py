"""The capability an app is prepared to run for a decision."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Intent:
    capability: str
    args: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"capability": self.capability, "args": dict(self.args)}


__all__ = ["Intent"]
