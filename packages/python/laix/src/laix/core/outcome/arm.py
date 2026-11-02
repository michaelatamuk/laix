"""One choice the learner can pick, with an optional prior."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..values import clamp


@dataclass(frozen=True, slots=True)
class Arm:
    """One choice the learner can pick, with an optional prior."""

    id: str
    prior_mean: float = 0.5
    prior_weight: float = 1.0
    cost: float = 0.0
    risk: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "prior_mean", clamp(self.prior_mean))
        object.__setattr__(self, "prior_weight", max(0.0, float(self.prior_weight)))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["Arm"]
