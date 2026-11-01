# Live Context

Live Context is the perception side of LAIX: what the layer can see, how often it looks, and what
looking costs. The app supplies detectors and events; LAIX supplies the loop, the admission rule and
the frame.

## Detector contract

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
| `name` | unique detector name |
| `tier` | `cheap` or `deep` |
| `cost` | cost of one call |
| `latency_ms` | time one call takes |
| `information_gain` | expected reduction in uncertainty, `0..1` |
| `detect(event)` | return zero or more detections |

`CallableDetector` wraps a plain function for tests and small adapters. A vision, audio or streaming
SDK stays inside the detector adapter.

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

1. Every cheap detector runs on every event.
2. A deep detector runs only when gain, weighted by uncertainty, clears the threshold.
3. Cost and latency must fit the budget.
4. The frame records what ran, what was skipped, why, and the remaining uncertainty.

The default budget admits at most two deep calls, spends at most `1.0`, and caps latency at `500 ms`.
A host can pass another `Budget`.

## Frames and streams

```python
frames = context.feed(events, uncertainty=0.7)
latest = context.latest
```

A `PerceptionFrame` contains:

| Field | Meaning |
|---|---|
| `subject`, `at` | event identity |
| `detections` | what the admitted detectors found |
| `allowed` | detectors that ran |
| `skipped` | detector name, reason and gain for each skipped call |
| `uncertainty` | remaining uncertainty after the observations |
| `deep_calls`, `cost` | resource use for this frame |

## TypeScript

The TypeScript package mirrors the contract:

```ts
import { CallableDetector, LiveContext } from "laix";

const context = new LiveContext([
  new CallableDetector("motion", (event) => [{ id: "d-1", detector: "motion", kind: "presence", subject: event.subject, at: event.at }], { informationGain: 0.2 }),
]);
```

## Driving the clock

The host drives time. A live loop calls `perceive` on each event; a batch job calls `feed`. Both
produce the same frame shape.

## Example

`examples/python/runtime/live_context.py` runs a cheap detector, an admitted deep detector and a deep
detector skipped for latency:

```text
('motion', 'read-label') ('transcribe',) 2 0.097
```
