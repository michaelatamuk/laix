"""Streaming app-kit surface: the live decision loop above the stateless core."""

from .session import (
    FULL_POLICIES,
    LATE_POLICIES,
    ManualClock,
    Refiner,
    StreamSession,
    StreamStats,
)
from .sources import from_queue, from_sync
from .window import TumblingWindow, WindowBatch
from .bench import StreamBenchResult, prometheus, run_stream_bench

__all__ = [
    "FULL_POLICIES",
    "LATE_POLICIES",
    "ManualClock",
    "Refiner",
    "StreamBenchResult",
    "StreamSession",
    "StreamStats",
    "TumblingWindow",
    "WindowBatch",
    "from_queue",
    "from_sync",
    "prometheus",
    "run_stream_bench",
]
