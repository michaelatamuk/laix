# Live Context

Live Context is the perception side of LAIX: what the layer can see, how often it looks, and how much
looking costs. It is a deterministic reference implementation. The app supplies detectors and event
streams; LAIX supplies the loop, the admission rule and the frame.

## Contract

```python
from laix import Detector, Detection, PerceptionEvent

class MyDetector:
    name = "read-label"
    tier = "deep"
    cost = 0.1
    latency_ms = 200
    information_gain = 0.9

    def detect(self, event: PerceptionEvent) -> list[Detection]: ...
```

A detector declares:

| Field | Meaning |
|---|---|
| `name` | unique detector name |
| `tier` | `cheap` or `deep` |
| `cost` | what one call costs |
| `latency_ms` | how long the call takes |
| `information_gain` | expected reduction in uncertainty, `0..1` |
| `detect(event)` | return zero or more detections |

`CallableDetector` wraps a plain function for tests and small adapters.

## The loop

`LiveContext` keeps detectors and frames:

```python
from laix import LiveContext, PerceptionEvent

context = LiveContext([cheap_detector, deep_detector])
frame = context.perceive(
    PerceptionEvent(subject="kitchen", at="2026-11-01T10:00:00+00:00"),
    uncertainty=0.8,
)
```

The rule is:

1. every cheap detector runs on every event;
2. a deep detector runs only when its gain, weighted by uncertainty, clears the threshold;
3. cost and latency must fit the budget;
4. the frame records what ran, what was skipped, why, and the remaining uncertainty.

The default budget admits at most two deep calls, spends at most `1.0`, and caps latency at
`500 ms`. That makes the reference loop sub-second. A host can pass another `Budget`.

## Frames and streams

```python
frames = context.feed(events, uncertainty=0.7)
latest = context.latest
```

`PerceptionFrame` is the layer's view of one event:

- subject and time;
- detections;
- allowed and skipped detectors;
- remaining uncertainty;
- deep-call count and cost.

## Boundary

The app owns cameras, microphones, sensors, transports and domain-specific detectors. LAIX owns the
admission rule, the frame shape and the uncertainty update. LAIX does not import a vision, audio or
streaming SDK.

The host drives the clock. A real sub-second loop ticks `perceive` on each event; a batch job calls
`feed`. Both produce the same frame shape.

## Example

`examples/python/runtime/live_context.py` runs a cheap detector, an admitted deep detector and a deep
detector skipped for latency:

```text
('motion', 'read-label') ('transcribe',) 2 0.097
```
