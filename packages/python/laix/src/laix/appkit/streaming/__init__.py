"""Streaming app-kit surface: the live decision loop above the stateless decision layer."""

from .session import (
    FULL_POLICIES,
    LATE_POLICIES,
    ManualClock,
    Refiner,
    StreamSession,
    StreamStats,
)
from .sources import DeadLetter, DeadLetterQueue, from_ndjson, from_queue, from_sse, from_sync
from .window import TumblingWindow, WindowBatch
from .bench import StreamBenchResult, prometheus, run_stream_bench
from .checkpoint import (
    FileStreamCheckpointStore,
    InMemoryStreamCheckpointStore,
    StreamCheckpointStore,
)
from .timeline import DecisionTimeline, TimelineError, TimelineReport

__all__ = [
    "FULL_POLICIES",
    "LATE_POLICIES",
    "DeadLetter",
    "DeadLetterQueue",
    "DecisionTimeline",
    "ManualClock",
    "Refiner",
    "StreamBenchResult",
    "StreamCheckpointStore",
    "FileStreamCheckpointStore",
    "InMemoryStreamCheckpointStore",
    "StreamSession",
    "StreamStats",
    "TimelineError",
    "TimelineReport",
    "TumblingWindow",
    "WindowBatch",
    "from_queue",
    "from_sync",
    "from_ndjson",
    "from_sse",
    "prometheus",
    "run_stream_bench",
]
