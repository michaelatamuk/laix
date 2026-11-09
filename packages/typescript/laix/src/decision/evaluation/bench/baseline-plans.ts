import type { ActionOption } from "../../contracts.ts";
import type { PlannerResult } from "../../contract/planner.ts";

export function baselinePlan(option: ActionOption, reasonCode: string, rationale: string): PlannerResult {
  return {
    verb: option.verb,
    confidence: 1,
    reasonCode,
    rationale,
    actionId: option.id,
    requiresApproval: Boolean(option.requiresApproval || option.destructive),
    reversible: option.reversible ?? true,
    score: option.expectedBenefit ?? 0.5,
  };
}

export function baselineWait(reasonCode: string, rationale: string): PlannerResult {
  return { verb: "wait", confidence: 1, reasonCode, rationale, score: 0 };
}
