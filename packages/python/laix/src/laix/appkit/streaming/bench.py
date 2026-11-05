"""Export stream counters and run a deterministic throughput bench."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from ...core.decisions import Decision, DecisionRequest
from .session import StreamSession, StreamStats


def prometheus(stats: StreamStats, *, prefix: str = "laix_stream") -> str:
    """Render the counters in Prometheus text format; no extra dependency."""
    lines: list[str] = []
    for key, value in stats.snapshot().items():
        name = f"{prefix}_{key}"
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True, slots=True)
class StreamBenchResult:
    decisions: tuple[Decision, ...]
    elapsed_ms: float
    throughput_per_second: float
    stats: dict[str, int | float]


def run_stream_bench(
    session: StreamSession,
    requests: Iterable[DecisionRequest],
) -> StreamBenchResult:
    """Replay requests through the session and report time and counters."""
    started = time.perf_counter()
    decisions = tuple(session.replay(requests))
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    throughput = len(decisions) / (elapsed_ms / 1000.0) if elapsed_ms > 0 else 0.0
    return StreamBenchResult(
        decisions=decisions,
        elapsed_ms=round(elapsed_ms, 3),
        throughput_per_second=round(throughput, 3),
        stats=session.stats.snapshot(),
    )


__all__ = ["StreamBenchResult", "prometheus", "run_stream_bench"]
