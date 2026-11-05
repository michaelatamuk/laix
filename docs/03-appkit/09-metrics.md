# Metrics

The app kit exposes stream counters and latency percentiles. It renders Prometheus text with the standard library.

## Counters

`StreamStats.snapshot()` returns:

| Group | Counters |
|---|---|
| Input | `observed`, `late`, `duplicates` |
| Output | `decided`, `dropped`, `suppressed`, `shed`, `expired` |
| Flow | `throttled`, `provisional`, `revised`, `refine_timeouts` |
| Latency | `latency_p50`, `latency_p95`, `latency_p99` |

## Prometheus

```python
from laix import prometheus

text = prometheus(stream.stats)
```

Each counter becomes `laix_stream_<name>` with a gauge type.

## What to alert on

- rising `duplicates` — the source is repeating event ids;
- rising `shed` — the per-window budget is too small;
- rising `expired` — decisions are missing their deadline;
- rising `refine_timeouts` — the deep path is too slow;
- rising `latency_p95` / `latency_p99` — the decision path is degrading;
- falling `decided` with steady `observed` — events are being suppressed or dropped.

## Bench

`run_stream_bench(session, requests)` reports decisions, elapsed time, throughput and the same
counters. See [bench](08-bench.md).

## Examples

- Python: `examples/python/04-stream/metrics.py`
- TypeScript: `examples/typescript/04-stream/metrics.mts`

## Boundary

Metrics describe stream behavior. Use generic labels and keep subject, customer id and message
content out of metric names.
