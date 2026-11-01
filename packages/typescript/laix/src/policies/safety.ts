import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class SafetyConstrainedPolicy {
  name = "safety-constrained.v1";
  version = "0.6.1";

  decide(request: DecisionRequest): Decision[] {
    if (Boolean(value(request, "safety_blocked", false))) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "safety_blocked", rationale: "a hard safety constraint blocks action", confidence: 1 })];
    }
    const riskLimit = numberValue(request, "risk_limit", 0.2);
    const options = (value(request, "options", []) as Record<string, unknown>[]) ?? [];
    const safe = options.filter((item) => Number(item.risk ?? 0) <= riskLimit);
    if (safe.length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "no_safe_option", rationale: "every available option exceeds the risk limit", confidence: 0.9 })];
    }
    const best = [...safe].sort((a, b) => {
      const score = (item: Record<string, unknown>) => Number(item.benefit ?? 0) - Number(item.risk ?? 0) - 0.1 * Number(item.cost ?? 0);
      return score(b) - score(a);
    })[0];
    const benefit = Number(best.benefit ?? 0);
    const risk = Number(best.risk ?? 0);
    const id = String(best.id ?? "");
    return [makeDecision({
      policy: this.name,
      verb: benefit >= 0.5 ? "act" : "guide",
      reasonCode: benefit >= 0.5 ? "safe_action" : "safe_to_show",
      rationale: `choose ${id || "?"} with risk ${risk.toFixed(2)} inside the limit ${riskLimit.toFixed(2)}`,
      confidence: Math.min(0.98, 0.55 + benefit * 0.4),
      intent: { capability: "act", args: { id } },
      score: benefit - risk,
      requiresApproval: Boolean(best.requires_approval ?? best.destructive ?? false),
      actionId: id,
    })];
  }
}
