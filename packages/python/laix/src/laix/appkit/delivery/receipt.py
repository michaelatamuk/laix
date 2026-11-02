"""The receipt an app can persist after trying to deliver a decision."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

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
        return asdict(self)


__all__ = ["DELIVERY_STATUSES", "DeliveryReceipt"]
