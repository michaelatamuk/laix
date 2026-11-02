"""A capability level, not a model name."""

from __future__ import annotations

from dataclasses import dataclass

CAPABILITY_LEVELS: tuple[str, ...] = ("fast", "balanced", "deep")


@dataclass(frozen=True, slots=True)
class Capability:
    """A capability level, not a model name."""

    level: str
    modalities: tuple[str, ...] = ()
    max_latency_ms: int | None = None
    max_cost: float | None = None

    def __post_init__(self) -> None:
        if self.level not in CAPABILITY_LEVELS:
            raise ValueError(f"unknown capability level: {self.level!r}")


__all__ = ["CAPABILITY_LEVELS", "Capability"]
