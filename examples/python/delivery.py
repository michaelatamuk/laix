"""LAIX decides to show something. The app owns the transport.

The result is:

    skipped email

- skipped: the null transport records a receipt without sending.
- email: the channel the app asked for.
"""

from laix import Context, DecisionRequest, Layer, NullDelivery, Signal
from datetime import datetime, timezone

decision = Layer().decide(
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
        context=Context(now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc), quiet_hours=None),
    )
)[0]

delivery = NullDelivery()
receipt = delivery.deliver(decision, "Electricity bill due tomorrow", channel="email")

print(receipt.status, receipt.channel)
