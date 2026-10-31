"""Compare a policy against expected decisions, case by case.

The result is:

    2 2 1.0

- 2: two cases were compared.
- 2: both decisions matched.
- 1.0: full agreement.
"""

from laix import Case, DecisionRequest, Layer, LayerDecision, compare_decisions, iso


class AlwaysWait:
    name = "always-wait"
    version = "1.0"

    def decide(self, request):
        return [
            LayerDecision(
                verb="wait",
                confidence=0.5,
                reason_code="policy_rule",
                rationale="this policy always waits",
            )
        ]


def decide(request):
    return Layer(policy=AlwaysWait()).decide(request)


cases = (
    Case(
        id="case-1",
        request=DecisionRequest(subject="one", at=iso()),
        expected=({"verb": "wait", "reason_code": "policy_rule"},),
    ),
    Case(
        id="case-2",
        request=DecisionRequest(subject="two", at=iso()),
        expected=({"verb": "wait", "reason_code": "policy_rule"},),
    ),
)

report = compare_decisions(cases, decide)
print(report.total, report.passed, report.agreement_rate)
