"""A high-severity risk signal asks LAIX whether to surface it now."""

from __future__ import annotations

from datetime import datetime, timezone

from laix import Context, DecisionRequest, Layer, Signal

decision = Layer().decide(
    DecisionRequest(
        subject="power plan review",
        at="2026-11-01T10:00:00+00:00",
        signals=(
            Signal(
                id="risk-1",
                kind="power",
                title="The power plan is below the required load",
                severity="high",
                confidence=0.9,
                due="2026-11-03T09:00:00+00:00",
                evidence_refs=("power-study-4",),
            ),
        ),
        context=Context(
            now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            quiet_hours=("22:00", "06:00"),
            min_severity="medium",
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.score)
