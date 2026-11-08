"""Keep a decision timeline with revisions and late-event checks."""

from __future__ import annotations

from laix import Decision, DecisionTimeline

timeline = DecisionTimeline()
timeline.add(
    Decision(
        verb="guide",
        confidence=0.8,
        reason_code="stream",
        rationale="a first decision",
        decision_id="d1",
        stream_id="desk",
        event_time="2026-11-01T10:00:00+00:00",
    )
)
timeline.add(
    Decision(
        verb="act",
        confidence=0.9,
        reason_code="stream",
        rationale="a revision",
        decision_id="d2",
        stream_id="desk",
        event_time="2026-11-01T10:01:00+00:00",
        revision=1,
        supersedes="d1",
    )
)

report = timeline.report()
latest = timeline.latest()
history = ",".join(item.decision_id for item in timeline.history("d2"))
print(report.decisions, report.chains, latest.decision_id, history)
