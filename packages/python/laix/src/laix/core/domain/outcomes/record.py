"""Whether a decision helped, measured against a named metric."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...support.serialize import to_primitive
from ...support.time import iso
from ...support.version import SCHEMA_VERSION
from .outcome_label import OutcomeLabel


OUTCOME_LABELS: tuple[str, ...] = tuple(label.value for label in OutcomeLabel)

OUTCOME_DIRECTIONS: tuple[str, ...] = ("higher-better", "lower-better")


@dataclass(frozen=True, slots=True)
class Outcome:
    """Whether a decision helped, measured against a named metric."""

    id: str
    decision_id: str
    metric: str
    before: float
    after: float
    delta: float
    label: str
    attributed: bool = False
    direction: str = "higher-better"
    evidence: dict[str, Any] = field(default_factory=dict)
    measured_at: str = field(default_factory=iso)
    note: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.label not in OUTCOME_LABELS:
            raise ValueError(f"unknown outcome label: {self.label}")
        if self.direction not in OUTCOME_DIRECTIONS:
            raise ValueError(f"unknown outcome direction: {self.direction}")

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["OUTCOME_DIRECTIONS", "OUTCOME_LABELS", "Outcome", "OutcomeLabel"]
