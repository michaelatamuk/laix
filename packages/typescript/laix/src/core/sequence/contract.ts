import type { ActionOption } from "../contracts.ts";
import type { Commitment } from "../commitments/commitments.ts";
import type { HumanAttentionBudget } from "../planners/human-attention/human-attention-budget.ts";

export interface DecisionStep {
  at: string;
  options: ActionOption[];
}

export interface DecisionScenario {
  steps: DecisionStep[];
  commitments?: Commitment[];
  humanAttentionBudget?: HumanAttentionBudget | null;
  openPenalty?: number;
}

export interface DecisionPlan {
  actions: string[];
  score: number;
  attentionSpent: number;
  violations: string[];
  nodes: number;
  optimal: boolean;
}

export interface SequencePlanner {
  readonly name: string;
  plan(scenario: DecisionScenario): DecisionPlan;
}
