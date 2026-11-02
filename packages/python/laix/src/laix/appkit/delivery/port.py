"""The delivery port: the app owns the transport."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .receipt import DeliveryReceipt


@runtime_checkable
class DeliveryPort(Protocol):
    """An app-supplied transport."""

    def deliver(self, decision: Any, message: Any, *, channel: str = "default") -> DeliveryReceipt:
        ...


__all__ = ["DeliveryPort"]
