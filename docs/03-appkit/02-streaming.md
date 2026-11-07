# Streaming decisions

The core is stateless: `decide(request)` returns one answer. A live app needs a
loop around that call — event time, a cooldown, a bounded buffer and decisions
that can be revised. `StreamSession` is that loop. It lives in the app kit and
calls the same core. The timeline and checkpoints are how
[decision continuity](../02-core/10-decision-continuity.md) survives a stream.

## Words used here

| Word | Meaning |
|---|---|
| **Event time** | When the event happened: `DecisionRequest.at`. The session uses it as its clock. |
| **Watermark** | The time boundary before which an event counts as late. |
| **Cadence** | `cooldown_ms`: the shortest gap between two decisions. |
| **Backpressure** | `observe_wait` waits for buffer space. |
| **Hysteresis** | `hysteresis_ms`: suppress a repeated decision inside the window. |
| **Provisional** | A fast decision that a later revision can replace. |
| **Revision** | A decision that supersedes an earlier one. |
| **Checkpoint** | A snapshot of the stream that can be resumed. |
| **Coalesce** | Collapse a busy feed; the newest event wins inside the window. |
| **NDJSON** | Newline-delimited JSON: one event per line. |
| **SSE** | Server-sent events: a one-way HTTP stream of events. |

```python
import asyncio

from laix import DecisionRequest, Layer

async def main() -> None:
    layer = Layer()
    stream = layer.stream(stream_id="desk", capacity=8, cooldown_ms=500)

    stream.observe(
        DecisionRequest(
            subject="a signal",
            at="2026-11-01T10:00:00+00:00",
            signals=(signal,),
            context=context,
        )
    )
    stream.close()

    async for decision in stream.decisions():
        print(decision.verb, decision.reason_code, decision.stream_id)

asyncio.run(main())
```

A stream can also carry the live-loop controls:

```python
stream = layer.stream(
    capacity=8,
    cooldown_ms=500,
    hysteresis_ms=2_000,
    max_decisions_per_window=20,
    budget_window_ms=60_000,
)

async for decision in stream.feed(events, coalesce_ms=200):
    print(decision.verb, decision.status, decision.revision)

first = await stream.observe_refined(request, deep_decide)
```

`feed` coalesces a busy source; `observe_refined` emits a provisional decision, awaits the deep path, then emits its revision.

For aggregation, close a tumbling window and decide the batch:

```python
from laix import DecisionRequest, TumblingWindow

window = TumblingWindow(window_ms=10_000)
for batch in window.add(request):
    aggregate = DecisionRequest(
        subject=f"{len(batch.events)} events",
        at=batch.end.isoformat(),
    )
    ...
```

Or let the session do it:

```python
async for decision in stream.feed_windows(
    events,
    window_ms=10_000,
    on_window=lambda batch: DecisionRequest(
        subject=f"{len(batch.events)} events",
        at=batch.end.isoformat(),
    ),
):
    ...
```

For operations:

```python
from laix import FileStreamCheckpointStore, prometheus, run_stream_bench

store = FileStreamCheckpointStore("./checkpoints")
stream.save(store, "case-1")
stream.resume(store, "case-1")

print(prometheus(stream.stats))
result = run_stream_bench(stream, requests)
print(result.decisions, result.elapsed_ms, result.throughput_per_second)
```

## What the session owns

| Concern | Rule |
|---|---|
| **Event time** | `DecisionRequest.at` is the event time. A decision carries it as `event_time`. |
| **Dedupe** | `DecisionRequest.event_id` plus `dedupe_ms`; a repeated id is counted as a duplicate and dropped. |
| **Late events** | An event behind the watermark is dropped by default; pass `late="accept"` to keep it. |
| **Cadence** | `cooldown_ms` suppresses a decision that arrives too soon. `force=True` bypasses it. |
| **Buffer** | `capacity` bounds the queue. `on_full` is `latest_wins`, `drop_oldest` or `drop_newest`. |
| **Backpressure** | `await observe_wait(request)` waits for buffer space. |
| **Hysteresis** | `hysteresis_ms` suppresses the same decision batch inside the window. |
| **Budget** | `max_decisions_per_window` + `budget_window_ms`; `force=True` bypasses it and `stats.shed` counts the rest. |
| **Revisions** | `revise(previous, request)` returns a decision with `revision + 1` and `supersedes`. |
| **Deep path** | `observe_refined(request, refine, timeout_ms=...)` emits `provisional`, awaits `refine`, then emits its revision; a timeout finalises the provisional. |
| **Feed** | `feed(events, coalesce_ms=...)` observes an async stream; the newest event wins inside the window. |
| **Windows** | `TumblingWindow(window_ms)` closes a batch on the event clock; `feed_windows(..., on_window=...)` decides each closed batch. |
| **Provisional** | `observe(request, status="provisional")` marks a fast decision that a revision can replace. |
| **Deadline** | A decision made after `deadline` is emitted as `provisional` and counted as expired. |
| **Replay** | `replay(requests)` runs the same sequence with event time as the clock, without filling the buffer. |
| **Trace and record** | Each decision gets a `trace_id` and a trace; a `recorder` callback receives every emitted decision for a `DecisionRecord`. |
| **Checkpoint** | `snapshot()` / `restore()` keep the watermark, cadence, counters, buffered decisions and traces. `StreamCheckpointStore` saves a snapshot; in-memory and file stores are included. A session created with an explicit `stream_id` refuses a checkpoint from another stream. |
| **Sources** | `from_queue`, `from_sync`, `from_ndjson` and `from_sse` adapt a queue, iterable or event stream to `feed`. NDJSON and SSE accept async or sync iterables, are strict by default, and can retain malformed frames in a `DeadLetterQueue` with `strict=False`. |
| **Operations** | `prometheus(stats)` exports counters; `run_stream_bench(session, requests)` reports throughput. |
| **Stats** | `stats` counts observed, decided, late, throttled, dropped, expired, suppressed, shed, duplicates, refine timeouts, provisional and revised, and reports p50/p95/p99 decision latency. |

## Decision timeline

`DecisionTimeline` keeps the decisions a session emits and enforces the revision semantics. Pass it
to `StreamSession(..., timeline=timeline)` and the session feeds it automatically:

- a root decision has revision 0 and no predecessor;
- a revision points to the decision it supersedes and uses the next number;
- a revision cannot move backwards in event time or switch streams;
- duplicate ids are rejected.

```python
from laix import DecisionTimeline, StreamSession

timeline = DecisionTimeline()
session = StreamSession(decide, timeline=timeline)

# ... observe events through the session ...

print(timeline.report().to_dict())
print(timeline.current())
print(timeline.history("d2"))
```

`report()` returns the number of decisions, open chains, superseded decisions and any issues.
`current()` returns the latest decision in each chain; `late(watermark)` returns decisions before
the watermark. The timeline is append-only.

## Contract fields

`Decision` carries the stream fields, all additive:

| Field | Meaning |
|---|---|
| `stream_id` | The session that produced the decision. |
| `event_time` | When the event happened. |
| `deadline` | When the decision had to be made. |
| `valid_until` | How long the decision applies. |
| `supersedes` | The decision this one replaces. |
| `revision` | `0` for the first decision, then `1`, `2`, … |
| `status` | `final`, `provisional` or `superseded`. |

`DecisionRequest` also accepts `event_id` (for dedupe), `deadline` and `valid_until`; the session
copies the deadline and validity onto the decisions it produces.

## Boundary

`StreamSession` wraps `decide` in event-time and flow control. The core stays stateless, and every
decision still goes through one policy and one contract. The session adds the live-loop concerns
around it: time, cadence, buffering and revision.

Use `decide` or `Layer.decide` for a one-shot answer. Use `Layer.stream` when
the host has a stream of events and needs decisions over time.

Call `observe` from the event loop that consumes `decisions`. `replay` is for
a fresh session or an incident review: it uses event time as the clock and
returns decisions without buffering.

Python and TypeScript both expose `StreamSession`; `Layer.stream` returns one.
