"""CUE — a show-production risk scan calls LAIX for timing.

CUE keeps its own risk detection, show store and delivery channels. It maps
each detected risk to one Signal and asks LAIX whether to show it now.

The result is:

    guide worth_surfacing 75.0

- guide: show the risk to the production office.
- worth_surfacing: the rule that says the risk is worth showing.
- 75.0: the score. The risk is high, due within three days, and 90% confirmed.
"""

from datetime import datetime, timezone

from laix import Context, DecisionRequest, Layer, Signal

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="CUE risk scan",
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
