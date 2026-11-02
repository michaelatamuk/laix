"""The host-driven detector loop and a function-backed detector."""

from __future__ import annotations

from .callable_detector import CallableDetector
from .loop import LiveContext

__all__ = ["CallableDetector", "LiveContext"]
