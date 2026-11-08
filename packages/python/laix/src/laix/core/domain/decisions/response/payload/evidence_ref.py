"""A reference to the evidence behind a decision."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    id: str
    kind: str = "reference"
    quote: str | None = None
    source: str | None = None
    confidence: float | None = None


__all__ = ["EvidenceRef"]
