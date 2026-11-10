"""Solve a discounted infinite-horizon MDP with policy iteration."""

from __future__ import annotations

from laix import MdpModel, MdpTransition, policy_iteration

model = MdpModel(
    states=("s0", "s1", "s2"),
    actions=("go", "stay"),
    transitions=(
        MdpTransition("s0", "go", "s1", 1.0, 1.0),
        MdpTransition("s0", "stay", "s0", 1.0, 0.0),
        MdpTransition("s1", "go", "s2", 1.0, 2.0),
        MdpTransition("s1", "stay", "s1", 1.0, 0.0),
    ),
    start="s0",
    discount=0.9,
    horizon=None,
)
result = policy_iteration(model)

print(result.policy["s0"], result.policy["s1"], round(result.values["s0"], 6))
