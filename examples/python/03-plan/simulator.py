"""Compare engines on the same scenario."""

from __future__ import annotations

from laix import Plan, Scenario, Simulator, compare_engines


class FixedEngine:
    def __init__(self, action: str) -> None:
        self.action = action

    def solve(self, problem) -> Plan:
        return Plan(
            verb="act",
            confidence=1.0,
            reason_code="fixed",
            rationale=f"always {self.action}",
            action_id=self.action,
        )


def step(state: str, action: str) -> tuple[str, float]:
    return state, 1.0 if action == "right" else 0.0


scenario = Scenario(
    name="left-or-right",
    simulator=Simulator(step, ("right", "wrong"), start="s", horizon=4),
    optimum=4.0,
)
report = compare_engines(
    {"right": FixedEngine("right"), "wrong": FixedEngine("wrong")},
    [scenario],
)
print(report.best(), report.summary()["right"]["mean_reward"], report.summary()["wrong"]["mean_gap"])
