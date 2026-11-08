# Perception

Core defines the perception records and the detector contract. The runtime loop lives in the app kit.

| Type | Fields |
|---|---|
| `Detection` | `id`, `detector`, `kind`, `subject`, `at`, `confidence`, `severity`, `payload` |
| `PerceptionEvent` | `subject`, `at`, `payload` |
| `PerceptionFrame` | `subject`, `at`, `detections`, `allowed`, `skipped`, `uncertainty`, `deep_calls`, `cost` |

`Detection.confidence` is clamped to `0..1`. `Detection.severity` uses the same severity words as
signal attention: `critical`, `high`, `medium`, `low` or `info`.

`Detector` is a protocol:

```python
class Detector(Protocol):
    name: str
    tier: str
    cost: float
    latency_ms: int
    information_gain: float

    def detect(self, event: PerceptionEvent) -> Iterable[Detection]: ...
```

`PerceptionFrame.to_dict()` uses `subject`, `at`, `detections`, `allowed`, `skipped`, `uncertainty`,
`deepCalls` and `cost`. It is the frame a detector loop returns after admission.

The app-kit runtime that drives detectors is `LiveContext` with `CallableDetector`. See
[Live Context](../../03-appkit/02-run/03-live-context.md).

## Related

- [Signals](../04-sensing/01-signals.md)
- [Resources](../04-sensing/02-resources.md)
- [Live Context](../../03-appkit/02-run/03-live-context.md)
- [App-kit build](../../03-appkit/01-build/01-integration.md)
