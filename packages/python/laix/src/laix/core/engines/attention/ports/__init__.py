"""The attention ports: clock, sink and recorder, plus their tiny defaults."""

from __future__ import annotations

from .clock import Clock
from .null_sink import NullSink
from .recorder import Recorder
from .sink import Sink
from .system_clock import SystemClock

__all__ = ["Clock", "NullSink", "Recorder", "Sink", "SystemClock"]
