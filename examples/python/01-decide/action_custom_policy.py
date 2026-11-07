"""Use a custom policy with the same DecisionClient API."""

from laix import DecisionRequest, DecisionClient, Decision


class AlwaysWait:
    name = "always-wait"
    version = "1.0"

    def decide(self, request):
        return [
            Decision(
                verb="wait",
                confidence=0.5,
                reason_code="policy_rule",
                rationale="this policy always waits",
            )
        ]


layer = DecisionClient(policy=AlwaysWait())
decision = layer.decide(
    DecisionRequest(subject="one decision", at="2026-11-01T10:00:00+00:00")
)[0]

print(decision.verb, decision.reason_code)
