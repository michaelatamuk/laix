import type { DecisionEngine, DecisionProblem, Plan } from "../contract/engine.ts";
import { baselinePlan, baselineWait } from "./baseline-plans.ts";

export class HighestBenefitPlanner implements DecisionEngine {
  readonly name = "benefit.v1";

  solve(problem: DecisionProblem): Plan {
    if (!problem.options.length) return baselineWait("no_options", "there are no options");
    return baselinePlan(
      [...problem.options].sort((left, right) =>
        (right.expectedBenefit ?? 0.5) - (left.expectedBenefit ?? 0.5),
      )[0]!,
      "highest_benefit",
      "the highest benefit was taken",
    );
  }
}
