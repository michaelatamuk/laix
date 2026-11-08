"""One thing a detector noticed in one event."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...support.values import clamp


@dataclass(frozen=True, slots=True)
class Detection:
    """One thing a detector noticed in one event."""

    id: str
    detector: str
    kind: str
    subject: str
    at: str
    confidence: float = 0.5
    severity: str = "low"
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", clamp(self.confidence))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["Detection"]
