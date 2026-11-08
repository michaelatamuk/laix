import { CABBPlanner } from "./cabb-planner.ts";
import type { DecisionPlan, DecisionScenario } from "./contract.ts";

function lexLess(left: string[], right: string[]): boolean {
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    if (left[index] !== right[index]) return left[index]! < right[index]!;
  }
  return left.length < right.length;
}

export class RolloutPlanner {
  readonly name = "sequence.rollout.v1";
  readonly planner: CABBPlanner;

  constructor(planner: CABBPlanner = new CABBPlanner()) {
    this.planner = planner;
  }

  plan(scenario: DecisionScenario): DecisionPlan {
    if (!scenario.steps.length) {
      return { actions: [], score: 0, attentionSpent: 0, violations: [], nodes: 0, optimal: true };
    }
    let best: DecisionPlan | null = null;
    let nodes = 0;
    for (const option of scenario.steps[0]!.options) {
      const actions = this.planner.greedyActions(scenario, [option.id]);
      if (actions.length !== scenario.steps.length) continue;
      let result: DecisionPlan;
      try {
        result = this.planner.evaluate(scenario, actions);
      } catch {
        continue;
      }
      nodes += 1;
      if (
        best === null ||
        result.score > best.score ||
        (result.score === best.score && lexLess(result.actions, best.actions))
      ) {
        best = result;
      }
    }
    if (best === null) {
      return { actions: [], score: 0, attentionSpent: 0, violations: [], nodes, optimal: false };
    }
    return {
      actions: best.actions,
      score: best.score,
      attentionSpent: best.attentionSpent,
      violations: best.violations,
      nodes,
      optimal: false,
    };
  }
}

export function rolloutDecisions(
  scenario: DecisionScenario,
  options: { planner?: CABBPlanner } = {},
): DecisionPlan {
  return new RolloutPlanner(options.planner).plan(scenario);
}
