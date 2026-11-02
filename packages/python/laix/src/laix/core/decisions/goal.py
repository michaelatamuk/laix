"""What the experience is trying to improve, with an explicit weight."""

from __future__ import annotations

from dataclasses import dataclass

from ..serialize import to_primitive
from ..values import clamp
from ..version import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class Goal:
    """What the experience is trying to improve, with an explicit weight."""

    id: str
    statement: str
    priority: float = 0.5
    metric: str = ""
    target: float | None = None
    deadline: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "priority", clamp(self.priority))

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["Goal"]
