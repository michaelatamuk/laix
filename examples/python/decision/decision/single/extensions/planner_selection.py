"""Choose a planner from a portfolio, then enforce its risk bound."""

from __future__ import annotations

from laix import (
    ActionOption,
    PlannerInput,
    PortfolioPlanner,
    RiskBoundedPlanner,
    UtilityPlanner,
)

problem = PlannerInput(
    subject="deploy",
    at="2026-11-01T10:00:00+00:00",
    options=(
        ActionOption(
            id="safe",
            verb="act",
            name="safe deploy",
            expected_benefit=0.6,
            params={"risk_bound": {"cvar_loss": 0.1}},
        ),
        ActionOption(
            id="risky",
            verb="act",
            name="risky deploy",
            expected_benefit=1.0,
            params={"risk_bound": {"cvar_loss": 0.9}},
        ),
    ),
    attributes={"planner": "risk"},
)
portfolio = PortfolioPlanner(
    {
        "utility": UtilityPlanner(),
        "risk": RiskBoundedPlanner(max_loss=0.5),
    }
)
plan = portfolio.solve(problem)

print(plan.attributes["planner"], plan.action_id, plan.attributes["cvar_loss"])
