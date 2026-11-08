"""Ordered evidence for one decision: input, policy, execution, outcome."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ....support.serialize import to_primitive
from ....support.time import iso
from ....support.version import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class Trace:
    """Ordered evidence for one decision: input, policy, execution, outcome."""

    id: str
    decision_id: str
    created_at: str = field(default_factory=iso)
    events: tuple[dict[str, Any], ...] = ()
    schema_version: str = SCHEMA_VERSION

    def with_event(self, stage: str, detail: dict[str, Any] | None = None, *, at: str | None = None) -> "Trace":
        event = {"at": at or iso(), "stage": stage, "detail": detail or {}}
        return Trace(id=self.id, decision_id=self.decision_id, created_at=self.created_at, events=(*self.events, event))

    def to_dict(self) -> dict:
        return to_primitive(self)


__all__ = ["Trace"]
