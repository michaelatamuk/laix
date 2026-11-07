# Metrics

The app kit exposes stream counters and latency percentiles. It renders Prometheus text with the
standard library. Prometheus is an open-source metrics and alerting system; the text output is
designed to be scraped by it.

## Counters

`StreamStats.snapshot()` returns:

| Group | Counters | Meaning |
|---|---|---|
| Input | `observed`, `late`, `duplicates` | Events seen, events behind the watermark and repeated event ids. |
| Output | `decided`, `dropped`, `suppressed`, `shed`, `expired` | Decisions emitted, dropped, suppressed, shed by the budget or expired. |
| Flow | `throttled`, `provisional`, `revised`, `refine_timeouts` | Cadence, provisional decisions, revisions and deep-path timeouts. |
| Latency | `latency_p50`, `latency_p95`, `latency_p99` | Decision latency percentiles. |

`StreamStats` is a dataclass; `snapshot()` returns the plain dict used by the exporter.

## Prometheus

```python
from laix import prometheus

text = prometheus(stream.stats)
print(text)
```

Each counter becomes `laix_stream_<name>` with a gauge type. Pass `prefix="my_app"` to change the
prefix.

```text
# TYPE laix_stream_observed gauge
laix_stream_observed 120
# TYPE laix_stream_decided gauge
laix_stream_decided 96
```

## What to alert on

| Signal | Likely cause | Response |
|---|---|---|
| Rising `duplicates` | The source is repeating event ids. | Check the source and the dedupe window. |
| Rising `shed` | The per-window budget is too small. | Raise the budget or reduce the event rate. |
| Rising `expired` | Decisions are missing their deadline. | Check the deep path and the deadline policy. |
| Rising `refine_timeouts` | The deep path is too slow. | Reduce depth, add a timeout or finalise the provisional. |
| Rising `latency_p95` / `latency_p99` | The decision path is degrading. | Inspect the policy, planner and model. |
| Falling `decided` with steady `observed` | Events are suppressed or dropped. | Check cadence, hysteresis and the buffer policy. |
| Rising `dropped` | The buffer is full and the overflow policy is dropping. | Raise capacity or apply backpressure. |

Alert on rates, not raw counters, and keep the window long enough to avoid noise.

## Bench

`run_stream_bench(session, requests)` reports decisions, elapsed time, throughput and the same
counters. See [Bench](01-bench.md) and [Streaming](../02-run/02-streaming.md).

## Examples

- Python: `examples/python/04-stream/metrics.py`
- TypeScript: `examples/typescript/04-stream/metrics.mts`

## TypeScript

TypeScript exports the same `prometheus` function and `StreamStats` shape.

## Boundary

Metrics describe stream behavior. Use generic labels and keep subject, customer id and message
content out of metric names. The host owns the metrics backend, retention and dashboards.

## Related

- [Streaming](../02-run/02-streaming.md) - the counters and the session.
- [Bench](01-bench.md) - stream bench.
- [Deployment](03-deployment.md) - observability and alerts.
