"""A shared human-attention budget."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HumanAttentionBudget:
    """A movable human-attention budget shared across decisions."""

    total: float = 1.0
    spent: float = 0.0

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("attention budget total must not be negative")
        if self.spent < 0:
            raise ValueError("attention budget spent must not be negative")

    def remaining(self) -> float:
        return max(0.0, self.total - self.spent)

    def spend(self, amount: float) -> float:
        if amount < 0:
            raise ValueError("attention spend must not be negative")
        self.spent = min(self.total, self.spent + amount)
        return self.remaining()

    def to_dict(self) -> dict[str, float]:
        return {"total": self.total, "spent": self.spent}

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "HumanAttentionBudget":
        return cls(
            total=float(payload.get("total", 1.0)),
            spent=float(payload.get("spent", 0.0)),
        )


__all__ = ["HumanAttentionBudget"]
