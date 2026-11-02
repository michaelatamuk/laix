"""One cheap or expensive measurement of the subject."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ....support.serialize import to_primitive
from ....support.values import clamp
from ....support.version import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class Observation:
    """One cheap or expensive measurement of the subject."""

    id: str
    at: str
    source: str
    kind: str
    confidence: float
    payload: dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    latency_ms: int = 0
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", clamp(self.confidence))

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["Observation"]
