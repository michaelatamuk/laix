# Live Context

Live Context is the perception side of LAIX. The app supplies detectors and events. LAIX decides what
to run and returns a frame.

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
| `name` | unique name |
| `tier` | `cheap` or `deep` |
| `cost` | cost of one call |
| `latency_ms` | time one call takes |
| `information_gain` | expected uncertainty reduction, `0..1` |
| `detect(event)` | return zero or more detections |

`CallableDetector` wraps a function for small adapters.

## Loop

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

The default budget allows two deep calls, cost `1.0` and latency `500 ms`.

## Frames

```python
frames = context.feed(events, uncertainty=0.7)
latest = context.latest
```

A frame has:

- subject and time;
- detections;
- allowed and skipped detectors;
- remaining uncertainty;
- deep-call count and cost.

TypeScript exports the same `LiveContext`, `CallableDetector` and `PerceptionFrame`.

## Clock

The host drives time. A live loop calls `perceive` on each event. A batch job calls `feed`.

## Example

`examples/python/runtime/live_context.py`:

```text
('motion', 'read-label') ('transcribe',) 2 0.097
```
