"""The delivery contract: port, receipt and a null implementation."""

from __future__ import annotations

from .null import NullDelivery
from .port import DeliveryPort
from .receipt import DELIVERY_STATUSES, DeliveryReceipt

__all__ = ["DELIVERY_STATUSES", "DeliveryPort", "DeliveryReceipt", "NullDelivery"]
