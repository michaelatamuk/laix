"""A delivery port that records receipts in memory and delivers nothing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .receipt import DeliveryReceipt


@dataclass(frozen=True, slots=True)
class NullDelivery:
    """A test double that records receipts in memory."""

    receipts: tuple[DeliveryReceipt, ...] = ()

    def deliver(self, decision: Any, message: Any, *, channel: str = "default") -> DeliveryReceipt:
        decision_id = str(getattr(decision, "decision_id", "") or "")
        receipt = DeliveryReceipt(
            id=f"dl-{len(self.receipts) + 1}",
            decision_id=decision_id,
            channel=channel,
            status="skipped",
            detail={"message": message},
        )
        object.__setattr__(self, "receipts", (*self.receipts, receipt))
        return receipt

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipts": [item.to_dict() for item in self.receipts],
        }


__all__ = ["NullDelivery"]
