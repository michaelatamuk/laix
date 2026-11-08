"""Outcome learning: feedback changes the next choice.

The result is:

    manual automatic 0.75

- manual: the first arm, because an untried arm is explored first.
- automatic: after manual failed and automatic worked, the learner switches.
- 0.75: the learned reward for automatic, including its prior.
"""

from laix import Arm, BanditPolicy, DecisionRequest, DecisionClient, UCBBandit, iso

policy = BanditPolicy(UCBBandit([Arm("manual"), Arm("automatic")]))
layer = DecisionClient(policy=policy)
request = DecisionRequest(subject="pick a mode", at=iso())

first = layer.decide(request)[0]

policy.record("manual", 0.0)
policy.record("automatic", 1.0)
second = layer.decide(request)[0]

print(first.action_id, second.action_id, round(policy.bandit.mean("automatic"), 2))
