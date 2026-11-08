# Live Context

Live Context is the perception part of LAIX. The app supplies detectors and events; LAIX decides
which detectors run and returns a frame. The frame becomes input to a decision request.

| Word | Meaning |
|---|---|
| **Event** | Something that happened, with a subject and a time. |
| **Detector** | App code that looks at an event and returns detections. |
| **Detection** | One thing a detector noticed. |
| **Frame** | LAIX's report for one event: what ran, what was skipped and what was found. |
| **Uncertainty** | How unsure the app is, from `0` to `1`. |
| **Budget** | The deep-call, cost and latency allowance for one event. |

The contracts live in `core/domain/perception`; the host-driven loop lives in
`appkit/live_context/loop.py`.

## Detector

```python
from laix import Detection, PerceptionEvent

class MyDetector:
    name = "read-label"
    tier = "deep"
    cost = 0.1
    latency_ms = 200
    information_gain = 0.9

    def detect(self, event: PerceptionEvent) -> list[Detection]: ...
```

| Field | Meaning |
|---|---|
| `name` | Unique name. |
| `tier` | `cheap` or `deep`. |
| `cost` | Cost of one call. |
| `latency_ms` | Time one call takes. |
| `information_gain` | Expected uncertainty reduction, `0..1`. |
| `detect(event)` | Return zero or more detections. |

`CallableDetector` wraps a function for small adapters. `LiveContext.register(detector)` validates the
name and the `detect` method; `detectors()` lists the registered names.

## The loop

```python
from laix import LiveContext, PerceptionEvent

context = LiveContext([cheap_detector, deep_detector])
frame = context.perceive(
    PerceptionEvent(subject="kitchen", at="2026-11-01T10:00:00Z"),
    uncertainty=0.8,
)
```

The rule:

1. Cheap detectors run on every event.
2. A deep detector runs when its gain, weighted by uncertainty, clears the threshold.
3. Cost and latency must fit the budget.
4. The frame records what ran, what was skipped and why.

The default budget allows two deep calls, cost `1.0` and latency `500 ms`:

```python
from laix import Budget, LiveContext

context = LiveContext(
    detectors,
    budget=Budget(max_deep_calls=2, max_cost=1.0, max_latency_ms=500),
)
```

The scheduler is the same `ResourceScheduler` used by `DecisionRuntime.schedule`. The resource model
is in [Resources](../../02-core/04-sensing/02-resources.md).

## Frames

```python
frames = context.feed(events, uncertainty=0.7)
latest = context.latest
```

A `PerceptionFrame` has:

- subject and time;
- detections;
- allowed and skipped detector names;
- remaining uncertainty;
- deep-call count and cost.

`feed(events, uncertainty=...)` returns a tuple of frames. `latest` is the last frame, or `None`
before the first call.

## Clock

The host drives time. A live loop calls `perceive` on each event. A batch job calls `feed`. Use
`ManualClock` for deterministic replay; see [Streaming](02-streaming.md).

## Example

`examples/python/appkit/run/live_context.py`:

```text
('motion', 'read-label') ('transcribe',) 2 0.097
```

The output is the detections, the detectors that ran, the deep-call count and the cost.

## TypeScript

TypeScript exports the same `LiveContext`, `CallableDetector` and `PerceptionFrame` surface.

## Boundary

Live Context is perception, not decision. It returns a frame; the app turns the frame into a
`DecisionRequest` and calls the core or `DecisionClient`. It does not choose a verb, execute an action or
deliver a result.

Use it when detectors are expensive or uncertain and the budget matters. For a single detector call,
call the detector directly.

## Related

- [Decision runtime](01-decision-runtime.md) - the decision loop after perception.
- [Streaming](02-streaming.md) - event time and the live loop.
- [Integration](../01-build/01-integration.md) - turning a frame into a request.
- [Resources](../../02-core/04-sensing/02-resources.md) - the budget and scheduler.
- [Foundation](../../02-core/07-support/02-support.md) - perception records.
