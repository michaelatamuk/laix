import { HumanAttentionBudget } from "../single/planners/human-attention/human-attention-budget.ts";
import { CABBPlanner } from "./cabb-planner.ts";
import type { DecisionScenario, DecisionStep } from "./contract.ts";

export interface ReplanResult {
  executed: string[];
  actions: string[];
  score: number;
  attentionSpent: number;
  violations: string[];
  nodes: number;
  optimal: boolean;
  reason: string;
}

export class ReplanPlanner {
  readonly name = "sequence.replan.v1";
  readonly planner: CABBPlanner;

  constructor(planner: CABBPlanner = new CABBPlanner()) {
    this.planner = planner;
  }

  replan(
    scenario: DecisionScenario,
    executed: readonly string[],
    options: { replacementStep?: DecisionStep } = {},
  ): ReplanResult {
    const prefix = [...executed];
    if (prefix.length > scenario.steps.length) {
      throw new Error("the executed prefix is longer than the scenario");
    }
    const { commitments, remaining } = this.planner.advance(scenario, prefix);
    const steps = scenario.steps.slice(prefix.length);
    if (options.replacementStep && steps.length) {
      steps[0] = options.replacementStep;
    }
    if (!steps.length) {
      return {
        executed: prefix,
        actions: [],
        score: 0,
        attentionSpent: 0,
        violations: [],
        nodes: 0,
        optimal: true,
        reason: "nothing left to replan",
      };
    }
    const budget = scenario.humanAttentionBudget;
    const nextBudget =
      budget === null || budget === undefined
        ? null
        : new HumanAttentionBudget({
            total: budget.total,
            spent: Math.max(0, budget.total - remaining),
          });
    const plan = this.planner.plan({
      steps,
      commitments,
      humanAttentionBudget: nextBudget,
      openPenalty: scenario.openPenalty,
    });
    return {
      executed: prefix,
      actions: plan.actions,
      score: plan.score,
      attentionSpent: plan.attentionSpent,
      violations: plan.violations,
      nodes: plan.nodes,
      optimal: plan.optimal,
      reason: `replanned ${steps.length} remaining steps`,
    };
  }
}

export function replanDecisions(
  scenario: DecisionScenario,
  executed: readonly string[],
  options: { planner?: CABBPlanner; replacementStep?: DecisionStep } = {},
): ReplanResult {
  return new ReplanPlanner(options.planner).replan(scenario, executed, {
    replacementStep: options.replacementStep,
  });
}
