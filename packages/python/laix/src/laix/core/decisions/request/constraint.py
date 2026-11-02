"""A budget, latency, risk, interruption or approval limit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...support.serialize import to_primitive
from ...support.version import SCHEMA_VERSION

CONSTRAINT_KINDS: tuple[str, ...] = (
    "latency",
    "cost",
    "risk",
    "interruption",
    "approval",
    "safety",
    "budget",
    "policy",
)


@dataclass(frozen=True, slots=True)
class Constraint:
    """A budget, latency, risk, interruption or approval limit.

    ``kind='approval'`` and ``value='required'`` mean a human must approve
    every destructive action.  ``hard=True`` means the policy may not violate
    it; ``hard=False`` means it is a preference used to score options.
    """

    id: str
    kind: str
    value: Any
    hard: bool = True
    statement: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.kind not in CONSTRAINT_KINDS:
            raise ValueError(f"unknown constraint kind: {self.kind}")

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["CONSTRAINT_KINDS", "Constraint"]
