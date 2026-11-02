"""A host task asks LAIX for one decision.

The host owns the task. LAIX only sees the generic request and returns the
decision, the confidence source and a portable basis.
"""

from laix import ActionOption, Belief, Constraint, DecisionRequest, Layer, Situation

options = (
    ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
    ActionOption(id="look", verb="observe", name="look closer", expected_benefit=0.5),
    ActionOption(id="ask", verb="ask", name="call the owner", expected_benefit=0.4),
    ActionOption(
        id="valve",
        verb="act",
        name="turn off the valve",
        expected_benefit=0.95,
        risk=0.05,
        reversible=True,
    ),
    ActionOption(id="manager", verb="escalate", name="call the manager", expected_benefit=0.7),
)

request = DecisionRequest(
    subject="bathroom leak",
    at="2026-11-01T10:00:00+00:00",
    situation=Situation(
        id="leak-1",
        at="2026-11-01T10:00:00+00:00",
        subject="bathroom leak",
        beliefs=(
            Belief(id="leak", proposition="water is leaking", confidence=0.9),
        ),
        constraints=(
            Constraint(id="risk-limit", kind="risk", value=0.2, hard=True),
        ),
        attributes={"urgency": 0.9},
    ),
    options=options,
    confidence=0.88,
    confidence_source="host-calibrated",
    calibrated=True,
)

decision = Layer().decide(request)[0]
print(
    decision.verb,
    decision.action_id,
    decision.confidence_source,
    decision.calibrated,
    decision.basis()[0]["kind"],
)
