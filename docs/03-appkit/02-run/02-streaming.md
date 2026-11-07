# Streaming

The core is stateless: `decide(request)` returns one answer. A live app needs a loop around that
call: event time, a cooldown, a bounded buffer and decisions that can be revised. `StreamSession` is
that loop. It lives in the app kit, calls the same core, and keeps
[decision continuity](../../02-core/04-continuity/01-decision-continuity.md) across events.

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
| **Window** | A tumbling batch closed on the event clock. |
| **Dead letter** | A malformed source frame kept for inspection. |
| **NDJSON** | Newline-delimited JSON: one event per line. |
| **SSE** | Server-sent events: a one-way HTTP stream of events. |

## The session

```python
import asyncio

from laix import DecisionRequest, DecisionClient

async def main() -> None:
    layer = DecisionClient()
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

`observe` returns the decisions it admitted. `decisions()` drains the buffer from an async loop. Call
`observe` from the same event loop that consumes `decisions`.

## Controls

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

`feed` coalesces a busy source; `observe_refined` emits a provisional decision, awaits the deep path,
then emits its revision.

| Option | Default | Meaning |
|---|---|---|
| `stream_id` | generated | The stream identifier stamped on decisions. |
| `capacity` | `32` | Buffer size. |
| `on_full` | `latest_wins` | `latest_wins`, `drop_oldest` or `drop_newest`. |
| `late` | `drop` | `drop` or `accept` an event behind the watermark. |
| `cooldown_ms` | `0` | Minimum gap between decisions. |
| `hysteresis_ms` | `0` | Suppress the same decision batch inside the window. |
| `dedupe_ms` | `0` | Drop a repeated `event_id` inside the window. |
| `max_decisions_per_window` | `None` | Per-window decision budget. |
| `budget_window_ms` | `1000` | Window for that budget. |
| `latency_samples` | `256` | Samples used for p50, p95 and p99. |
| `trace` | `True` | Attach a trace to each decision. |
| `recorder` | `None` | Callback that receives every emitted decision. |
| `timeline` | `None` | `DecisionTimeline` that receives decisions automatically. |
| `human_attention_budget` | `None` | Human-attention budget shared by the stream. |
| `clock` | `utcnow` | Clock used for event-time decisions; `ManualClock` for replay. |
| `id_factory` | `new_id` | Id factory for the generated stream id. |

`FULL_POLICIES = ("latest_wins", "drop_oldest", "drop_newest")` and
`LATE_POLICIES = ("drop", "accept")` are exported for validation.

## Windows

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

`WindowBatch` carries `start`, `end` and the tuple of `events`. `TumblingWindow.flush()` closes the
open window; `pending()` returns the number of buffered events.

## Sources and dead letters

```python
from laix import DeadLetterQueue, from_ndjson

dead = DeadLetterQueue(limit=10)

async for request in from_ndjson(lines, on_error=dead, strict=False):
    stream.observe(request)

print(dead.all())
```

`from_queue`, `from_sync`, `from_ndjson` and `from_sse` adapt a queue, iterable or event stream to
`feed`. NDJSON and SSE are strict by default. Pass `strict=False` and an `on_error` handler such as
`DeadLetterQueue` to keep malformed frames. `DeadLetter` carries `raw`, `error` and `at`.

## Checkpoints and operations

```python
from laix import FileStreamCheckpointStore, ManualClock, prometheus, run_stream_bench

store = FileStreamCheckpointStore("./checkpoints")
stream.save(store, "case-1")
stream.resume(store, "case-1")

print(prometheus(stream.stats))
result = run_stream_bench(stream, requests)
print(result.decisions, result.elapsed_ms, result.throughput_per_second)
```

`ManualClock` makes event time deterministic:

```python
from datetime import datetime, timezone
from laix import ManualClock

clock = ManualClock(datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc))
```

`StreamBenchResult` carries `decisions`, `elapsed_ms`, `throughput_per_second` and `stats`.
[Stores](../04-connect/01-stores.md) covers the checkpoint port;
[Metrics](../05-operate/02-metrics.md) covers the counters and alerts.

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
| **Budget** | `max_decisions_per_window` plus `budget_window_ms`; `force=True` bypasses it and `stats.shed` counts the rest. |
| **Revisions** | `revise(previous, request)` returns a decision with `revision + 1` and `supersedes`. |
| **Deep path** | `observe_refined(request, refine, timeout_ms=...)` emits `provisional`, awaits `refine`, then emits its revision; a timeout finalises the provisional. |
| **Feed** | `feed(events, coalesce_ms=...)` observes an async stream; the newest event wins inside the window. |
| **Windows** | `TumblingWindow(window_ms)` closes a batch on the event clock; `feed_windows(..., on_window=...)` decides each closed batch. |
| **Provisional** | `observe(request, status="provisional")` marks a fast decision that a revision can replace. |
| **Deadline** | A decision made after `deadline` is emitted as `provisional` and counted as expired. |
| **Replay** | `replay(requests)` runs the same sequence with event time as the clock, without filling the buffer. |
| **Trace and record** | Each decision gets a `trace_id` and a trace; a `recorder` callback receives every emitted decision for a `DecisionRecord`. |
| **Checkpoint** | `snapshot()` and `restore()` keep the watermark, cadence, counters, buffered decisions and traces. A session created with an explicit `stream_id` refuses a checkpoint from another stream. |
| **Sources** | `from_queue`, `from_sync`, `from_ndjson` and `from_sse` adapt a queue, iterable or event stream to `feed`. |
| **Operations** | `prometheus(stats)` exports counters; `run_stream_bench(session, requests)` reports throughput. |
| **Stats** | `stats` counts observed, decided, late, throttled, dropped, expired, suppressed, shed, duplicates, refine timeouts, provisional and revised, and reports p50, p95 and p99 decision latency. |

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

report = timeline.report()
print(report.to_dict())
print(timeline.current())
print(timeline.history("d2"))
```

`report()` returns a `TimelineReport` with `decisions`, `chains`, `superseded`, `issues` and
`valid`. `current()` returns the latest decision in each chain; `late(watermark)` returns decisions
before the watermark; `history(id)` returns the chain from the root. The timeline is append-only.

`DecisionTimeline.add` raises `TimelineError` for a duplicate id, a missing predecessor, a revision
gap, a stream mismatch or event time moving backwards. `assert_valid()` raises for any issue found
during a re-check.

## Contract fields

`Decision` carries the stream fields, all additive:

| Field | Meaning |
|---|---|
| `stream_id` | The session that produced the decision. |
| `event_time` | When the event happened. |
| `deadline` | When the decision had to be made. |
| `valid_until` | How long the decision applies. |
| `supersedes` | The decision this one replaces. |
| `revision` | `0` for the first decision, then `1`, `2`, ... |
| `status` | `final`, `provisional` or `superseded`. |

`DecisionRequest` also accepts `event_id` (for dedupe), `deadline` and `valid_until`; the session
copies the deadline and validity onto the decisions it produces.

## Boundary

`StreamSession` wraps `decide` in event-time and flow control. The core stays stateless, and every
decision still goes through one policy and one contract. The session adds the live-loop concerns
around it: time, cadence, buffering and revision.

Use `decide` or `DecisionClient.decide` for a one-shot answer. Use `DecisionClient.stream` when the host has a stream of
events and needs decisions over time.

Python and TypeScript expose `StreamSession`; `DecisionClient.stream` returns one. TypeScript also exports
`Refiner`, `Decider`, `StreamSessionOptions`, `SourceOptions`, `FullPolicy`, `LatePolicy`,
`DECISION_STATUSES` and `DecisionStatus`.

## Related

- [Decision runtime](01-decision-runtime.md) - the loop behind the session.
- [Live Context](03-live-context.md) - perception before the decision.
- [Stores](../04-connect/01-stores.md) - checkpoints and state.
- [Metrics](../05-operate/02-metrics.md) - counters, latency and alerts.
- [Bench](../05-operate/01-bench.md) - stream bench.
- [Decision continuity](../../02-core/04-continuity/01-decision-continuity.md) - the state carried across decisions.
