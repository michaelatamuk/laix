"""LAIX decides, the host executes, the receipt records what happened.

The result is:

    executed close the valve

- executed: the host ran the action.
- close the valve: the action named by the decision.

DecisionRuntime ties the policy, the execution bridge and the trace together.
"""

from laix import (
    ActionOption,
    Belief,
    DecisionRuntime,
    ExecutionBridge,
    Situation,
    iso,
)

options = (
    ActionOption(id="option-wait", verb="wait", name="keep watching", expected_benefit=0.1),
    ActionOption(
        id="option-close-valve",
        verb="act",
        name="close the valve",
        expected_benefit=0.95,
        risk=0.05,
        reversible=True,
    ),
)

bridge = ExecutionBridge(handlers={"close the valve": lambda action, context: {"done": action.name}})
runtime = DecisionRuntime(bridge=bridge)
decision = runtime.decide(
    Situation(
        id="sink-1",
        at=iso(),
        subject="kitchen sink",
        beliefs=(Belief(id="overflow", proposition="the sink is about to overflow", confidence=0.95),),
        attributes={"urgency": 0.9},
    ),
    options,
)

receipt = runtime.execute(decision, actor="agent")
print(receipt.status, receipt.action_name)
