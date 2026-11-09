import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class ReplanningPolicy {
  name = "replanning.v1";
  version = "0.8.0";

  decide(request: DecisionRequest): Decision[] {
    const plans = (value(request, "plans", []) as Record<string, unknown>[]) ?? [];
    const minSuccess = numberValue(request, "min_success", 0.5);
    const maxCost = numberValue(request, "max_cost", Number.POSITIVE_INFINITY);
    const riskWeight = numberValue(request, "risk_weight", 1);
    const feasible = plans.filter((plan) => Number(plan.success_probability ?? 0) >= minSuccess && Number(plan.cost ?? 0) <= maxCost);
    if (feasible.length === 0) {
      return [makeDecision({ policy: this.name, verb: "ask", reasonCode: "no_feasible_plan", rationale: "no plan meets the success and cost limits; ask for a changed constraint", confidence: 0.8 })];
    }
    const best = [...feasible].sort((a, b) => {
      const score = (plan: Record<string, unknown>) =>
        Number(plan.success_probability ?? 0) - riskWeight * Number(plan.cost ?? 0) - Number(plan.deadline_risk ?? 0);
      return score(b) - score(a);
    })[0];
    const success = Number(best.success_probability ?? 0);
    const id = String(best.id ?? "");
    return [makeDecision({ policy: this.name, verb: "act", reasonCode: "replan", rationale: `adopt ${id || "?"} with success probability ${success.toFixed(2)}`, confidence: Math.min(0.98, 0.5 + success * 0.4), intent: { capability: "adopt_plan", args: { id } }, score: success, requiresApproval: Boolean(best.requires_approval ?? false), actionId: id })];
  }
}
