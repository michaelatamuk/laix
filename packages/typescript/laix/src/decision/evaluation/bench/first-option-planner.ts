import type { Planner, PlannerInput, PlannerResult } from "../../contract/planner.ts";
import { baselinePlan, baselineWait } from "./baseline-plans.ts";

export class FirstOptionPlanner implements Planner {
  readonly name = "first.v1";

  solve(problem: PlannerInput): PlannerResult {
    const option = problem.options[0];
    if (!option) return baselineWait("no_options", "there are no options");
    return baselinePlan(option, "first_option", "the first option was taken");
  }
}
