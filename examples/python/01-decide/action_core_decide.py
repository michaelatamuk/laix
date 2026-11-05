"""Ask the core for one decision, with no app kit.

The result is:

    act policy_rule option-close-valve DEC-...

``decide`` selects the action engine from the request shape, returns the same
``Decision`` shape as the app kit, and gives it a decision id. There is no
runtime, trace, execution or record here; those live in ``laix.appkit``.
"""

from laix import ActionOption, Belief, DecisionRequest, Situation, decide, iso

decision = decide(
    DecisionRequest(
        subject="kitchen sink",
        at=iso(),
        situation=Situation(
            id="sink-1",
            at=iso(),
            subject="kitchen sink",
            beliefs=(
                Belief(
                    id="overflow",
                    proposition="the sink is about to overflow",
                    confidence=0.95,
                ),
            ),
            attributes={"urgency": 0.9},
        ),
        options=(
            ActionOption(id="option-wait", verb="wait", name="keep-watching", expected_benefit=0.1),
            ActionOption(
                id="option-close-valve",
                verb="act",
                name="close the valve",
                expected_benefit=0.95,
                risk=0.05,
                reversible=True,
            ),
        ),
    )
)[0]

print(decision.verb, decision.reason_code, decision.action_id, decision.decision_id)
