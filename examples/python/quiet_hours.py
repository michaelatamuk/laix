"""The same bill, now at 23:30. Should the app wake the user?

The result is:

    wait quiet_hours 84.0 True False

That means:

- wait: stay silent now.
- quiet_hours: quiet hours are active, so the item waits.
- 84.0: the score still says it is important.
- True: keep the item on record for the morning digest.
- False: do not deliver it now.

The bill is not critical, so quiet hours hold it. A critical item passes
quiet hours and reaches the user.
"""

from datetime import datetime, timezone

from laix import Context, DecisionRequest, Layer, Signal

layer = Layer()
decision = layer.decide(
    DecisionRequest(
        subject="electricity bill at night",
        at="2026-11-01T23:30:00+00:00",
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
            now=datetime(2026, 11, 1, 23, 30, tzinfo=timezone.utc),
            quiet_hours=("22:00", "06:00"),
            min_severity="medium",
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.score, decision.record, decision.deliver)
