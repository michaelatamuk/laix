"""One perception or model call the scheduler can admit."""

from __future__ import annotations

from dataclasses import dataclass

from ....support.values import clamp


@dataclass(frozen=True)
class SensingOption:
    name: str
    tier: str = "cheap"  # cheap | deep
    cost: float = 0.0
    latency_ms: int = 0
    information_gain: float = 0.0

    def __post_init__(self) -> None:
        if self.tier not in {"cheap", "deep"}:
            raise ValueError(f"unknown sensing tier: {self.tier}")
        object.__setattr__(self, "information_gain", clamp(self.information_gain))


__all__ = ["SensingOption"]
