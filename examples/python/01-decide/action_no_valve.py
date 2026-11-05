"""Water and electricity, with no safe valve to close.

The breaker crosses water and the valve is out of reach. The safe action set is
empty, so the safety boundary escalates to a qualified person.
"""

from laix import ActionOption, Belief, Constraint, DecisionRequest, Layer, Situation

decision = Layer().decide(
    DecisionRequest(
        subject="water near electricity",
        at="2026-11-01T10:00:00+00:00",
        situation=Situation(
            id="leak-1",
            at="2026-11-01T10:00:00+00:00",
            subject="water near electricity",
            beliefs=(
                Belief(id="leak", proposition="water is leaking", confidence=0.9),
                Belief(id="power", proposition="a socket is near the floor", confidence=0.9),
            ),
            constraints=(
                Constraint(id="risk-limit", kind="risk", value=0.2, hard=True),
            ),
            attributes={"urgency": 0.9, "safety_breached": True},
        ),
        options=(
            ActionOption(id="wait", verb="wait", name="wait", expected_benefit=0.1),
            ActionOption(id="look", verb="observe", name="look from the doorway", expected_benefit=0.5),
            ActionOption(id="guide", verb="guide", name="keep people out", expected_benefit=0.6),
            ActionOption(id="ask", verb="ask", name="call the owner", expected_benefit=0.4),
            ActionOption(
                id="breaker",
                verb="act",
                name="cross the wet floor to the breaker",
                expected_benefit=1.0,
                risk=0.9,
            ),
            ActionOption(id="manager", verb="escalate", name="call a qualified person", expected_benefit=0.7),
        ),
    )
)[0]

print(decision.verb, decision.action_id, decision.score)
print(decision.rationale)
for item in decision.constraints_applied:
    print("constraint", item)
