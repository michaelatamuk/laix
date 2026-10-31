"""A delivery port for attention decisions.

LAIX decides that something is worth showing. The app owns the transport:
in-app, email, Slack, SMS or a webhook. This module defines the small contract
between the decision and that transport, plus a receipt the app can persist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

DELIVERY_STATUSES: tuple[str, ...] = ("delivered", "skipped", "failed")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class DeliveryReceipt:
    id: str
    decision_id: str
    channel: str
    status: str
    at: str = field(default_factory=_now)
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in DELIVERY_STATUSES:
            raise ValueError(f"unknown delivery status: {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


@runtime_checkable
class DeliveryPort(Protocol):
    """An app-supplied transport."""

    def deliver(self, decision: Any, message: Any, *, channel: str = "default") -> DeliveryReceipt:
        ...


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


__all__ = ["DELIVERY_STATUSES", "DeliveryPort", "DeliveryReceipt", "NullDelivery"]
