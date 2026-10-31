"""A bill is due tomorrow. Should the app show it now?

The result is:

    guide worth_surfacing 84.0

That means:

- guide: show the bill to the user now. The user decides when to pay.
- worth_surfacing: the rule that says the bill is worth surfacing.
- 84.0: the policy score. A higher score means the item is more worth showing.

The bill is high severity, due within 24 hours, and confirmed with 95%
confidence. It is 10:00, so quiet hours do not apply.
"""

from datetime import datetime, timezone

from laix import Context, DecisionRequest, Layer, Signal

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="electricity bill",
        at="2026-11-01T10:00:00+00:00",
        signals=(
            Signal(
                id="bill-1",
                kind="deadline",
                title="Electricity bill due tomorrow",
                severity="high",
                confidence=0.95,
                due="2026-11-02T09:00:00+00:00",
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
