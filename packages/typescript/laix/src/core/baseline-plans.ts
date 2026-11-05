import type { ActionOption } from "./contracts.ts";
import type { Plan } from "./engine.ts";

export function baselinePlan(option: ActionOption, reasonCode: string, rationale: string): Plan {
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

export function baselineWait(reasonCode: string, rationale: string): Plan {
  return { verb: "wait", confidence: 1, reasonCode, rationale, score: 0 };
}
