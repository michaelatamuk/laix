"""A compact view of one decision timeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimelineReport:
    """A compact view of one timeline."""

    decisions: int
    chains: int
    superseded: int
    issues: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "decisions": self.decisions,
            "chains": self.chains,
            "superseded": self.superseded,
            "valid": self.valid,
            "issues": list(self.issues),
        }


__all__ = ["TimelineReport"]
