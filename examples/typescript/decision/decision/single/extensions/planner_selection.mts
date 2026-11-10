import {
  PortfolioPlanner,
  RiskBoundedPlanner,
  UtilityPlanner,
  type PlannerInput,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const problem: PlannerInput = {
  subject: "deploy",
  at: "2026-11-01T10:00:00Z",
  options: [
    {
      id: "safe",
      verb: "act",
      name: "safe deploy",
      expectedBenefit: 0.6,
      params: { risk_bound: { cvar_loss: 0.1 } },
    },
    {
      id: "risky",
      verb: "act",
      name: "risky deploy",
      expectedBenefit: 1,
      params: { risk_bound: { cvar_loss: 0.9 } },
    },
  ],
  attributes: { planner: "risk" },
};
const portfolio = new PortfolioPlanner({
  utility: new UtilityPlanner(),
  risk: new RiskBoundedPlanner(undefined, { maxLoss: 0.5 }),
});
const plan = portfolio.solve(problem);

console.log(plan.attributes?.planner, plan.actionId, plan.attributes?.cvar_loss);
