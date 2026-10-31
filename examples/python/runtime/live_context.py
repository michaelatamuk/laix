"""Live Context: cheap detectors always run, deep ones only when they pay off.

The result is:

    ('motion', 'read-label') ('transcribe',) 2 0.097

- motion: the cheap detector runs on every event.
- read-label: the deep detector is admitted inside the sub-second budget.
- transcribe: skipped because its latency exceeds the budget.
- 2: two detections were produced.
- 0.097: remaining uncertainty after the admitted checks.
"""

from laix import CallableDetector, Detection, LiveContext, PerceptionEvent

event = PerceptionEvent(
    subject="kitchen",
    at="2026-11-01T10:00:00+00:00",
    payload={"motion": True},
)


def found(name: str, confidence: float):
    def detect(item: PerceptionEvent):
        return [
            Detection(
                id=f"{name}-{item.at}",
                detector=name,
                kind="presence",
                subject=item.subject,
                at=item.at,
                confidence=confidence,
            )
        ]

    return detect


context = LiveContext(
    [
        CallableDetector("motion", found("motion", 0.8), information_gain=0.2),
        CallableDetector(
            "read-label",
            found("read-label", 0.95),
            tier="deep",
            cost=0.1,
            latency_ms=200,
            information_gain=0.9,
        ),
        CallableDetector(
            "transcribe",
            found("transcribe", 0.9),
            tier="deep",
            cost=0.1,
            latency_ms=900,
            information_gain=0.9,
        ),
    ]
)

frame = context.perceive(event, uncertainty=0.8)
print(
    frame.allowed,
    tuple(item["name"] for item in frame.skipped),
    len(frame.detections),
    round(frame.uncertainty, 3),
)
