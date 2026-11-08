import type { Decision, DecisionRequest } from "../../../../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class AllocationPolicy {
  name = "allocation.v1";
  version = "0.8.0";

  decide(request: DecisionRequest): Decision[] {
    const requests = (value(request, "requests", []) as Record<string, unknown>[]) ?? [];
    const budget = numberValue(request, "budget", 0);
    const maxRisk = numberValue(request, "max_risk", 1);
    const candidates = requests
      .filter((item) => Number(item.cost ?? 0) <= budget && Number(item.risk ?? 0) <= maxRisk)
      .sort((a, b) => {
        const ratio = (item: Record<string, unknown>) => Number(item.value ?? 0) / Math.max(Number(item.cost ?? 0), 0.001);
        return ratio(b) - ratio(a);
      });

    const chosen: Record<string, unknown>[] = [];
    let spent = 0;
    let totalValue = 0;
    for (const item of candidates) {
      const cost = Number(item.cost ?? 0);
      if (spent + cost > budget) continue;
      chosen.push(item);
      spent += cost;
      totalValue += Number(item.value ?? 0);
    }
    if (chosen.length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "nothing_affordable", rationale: "no request fits the budget and risk limit", confidence: 0.8 })];
    }
    return [makeDecision({
      policy: this.name,
      verb: "act",
      reasonCode: "allocate",
      rationale: `fund ${chosen.length} request(s) for value ${totalValue.toFixed(2)} within budget ${budget.toFixed(2)}`,
      confidence: Math.min(0.95, 0.5 + (totalValue / Math.max(budget, 1)) * 0.2),
      intent: { capability: "allocate", args: { ids: chosen.map((item) => String(item.id ?? "")) } },
      score: totalValue,
      requiresApproval: Boolean(value(request, "requires_approval", false)),
    })];
  }
}
