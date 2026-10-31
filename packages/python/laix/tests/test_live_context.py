"""Live Context: detectors, admission and frames."""

from __future__ import annotations

from laix import (
    Budget,
    CallableDetector,
    Detection,
    LiveContext,
    PerceptionEvent,
)


def detection(detector: str, event: PerceptionEvent, confidence: float = 0.8) -> Detection:
    return Detection(
        id=f"{detector}-{event.at}",
        detector=detector,
        kind="presence",
        subject=event.subject,
        at=event.at,
        confidence=confidence,
    )


def cheap(event: PerceptionEvent):
    return [detection("motion", event)]


def test_cheap_runs_and_deep_is_admitted() -> None:
    context = LiveContext(
        [
            CallableDetector("motion", cheap, information_gain=0.2),
            CallableDetector(
                "read-label",
                lambda event: [detection("read-label", event, 0.95)],
                tier="deep",
                cost=0.1,
                latency_ms=200,
                information_gain=0.9,
            ),
        ]
    )
    frame = context.perceive(
        PerceptionEvent(subject="kitchen", at="2026-11-01T10:00:00+00:00"),
        uncertainty=0.8,
    )
    assert frame.allowed == ("motion", "read-label")
    assert frame.deep_calls == 1
    assert len(frame.detections) == 2
    assert frame.uncertainty < 0.8


def test_deep_is_skipped_when_latency_exceeds_the_sub_second_budget() -> None:
    context = LiveContext(
        [
            CallableDetector("motion", cheap, information_gain=0.2),
            CallableDetector(
                "transcribe",
                lambda event: [detection("transcribe", event)],
                tier="deep",
                cost=0.1,
                latency_ms=900,
                information_gain=0.9,
            ),
        ]
    )
    frame = context.perceive(
        PerceptionEvent(subject="kitchen", at="2026-11-01T10:00:00+00:00"),
        uncertainty=0.8,
    )
    assert frame.allowed == ("motion",)
    assert frame.deep_calls == 0
    assert frame.skipped[0]["name"] == "transcribe"


def test_feed_keeps_every_frame_and_exposes_latest() -> None:
    context = LiveContext([CallableDetector("motion", cheap, information_gain=0.2)])
    frames = context.feed(
        [
            PerceptionEvent(subject="one", at="2026-11-01T10:00:00+00:00"),
            PerceptionEvent(subject="two", at="2026-11-01T10:00:01+00:00"),
        ]
    )
    assert len(frames) == 2
    assert context.latest is frames[-1]
    assert context.latest.subject == "two"


def test_custom_budget_can_disable_deep_calls() -> None:
    context = LiveContext(
        [
            CallableDetector(
                "read-label",
                lambda event: [detection("read-label", event)],
                tier="deep",
                cost=0.1,
                latency_ms=100,
                information_gain=0.9,
            )
        ],
        budget=Budget(max_deep_calls=0),
    )
    frame = context.perceive(
        PerceptionEvent(subject="kitchen", at="2026-11-01T10:00:00+00:00"),
        uncertainty=0.9,
    )
    assert frame.allowed == ()
    assert frame.detections == ()
