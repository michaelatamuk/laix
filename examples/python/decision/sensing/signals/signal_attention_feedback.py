"""The person already dismissed this. Do not raise it again.

The result is:

    wait dismissed

- wait: stay silent.
- dismissed: the recorded feedback suppresses the signal.
"""

from datetime import datetime, timezone

from laix import SignalContext, DecisionRequest, SignalFeedback, DecisionClient, Signal

decision = DecisionClient().decide(
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
        context=SignalContext(
            now=datetime(2026, 11, 1, 10, 0, tzinfo=timezone.utc),
            quiet_hours=None,
            feedback={"bill-1": SignalFeedback(state="dismissed")},
        ),
    )
)[0]

print(decision.verb, decision.reason_code)
