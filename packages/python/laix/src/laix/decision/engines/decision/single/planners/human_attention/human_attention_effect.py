"""The human-attention cost of one option."""

from __future__ import annotations

from dataclasses import dataclass

from ......support.values import clamp


@dataclass(frozen=True, slots=True)
class HumanAttentionEffect:
    """The human-attention cost of one option."""

    interrupt_cost: float = 0.0
    requires_approval: bool = False
    escalates: bool = False
    interactive: bool = False
    approval_state: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "interrupt_cost", clamp(self.interrupt_cost))

    @property
    def cost(self) -> float:
        """A comparable attention cost: interruption, approval, escalation and contact."""
        return (
            self.interrupt_cost
            + (0.5 if self.requires_approval else 0.0)
            + (0.5 if self.escalates else 0.0)
            + (0.5 if self.interactive else 0.0)
        )

    @property
    def requires_attention(self) -> bool:
        return self.cost > 0.0 or self.requires_approval or self.escalates


__all__ = ["HumanAttentionEffect"]
