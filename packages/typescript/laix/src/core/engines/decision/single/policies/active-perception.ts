import type { Decision, DecisionRequest } from "../../../../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class ActivePerceptionPolicy {
  name = "active-perception.v1";
  version = "0.8.0";

  decide(request: DecisionRequest): Decision[] {
    const uncertainty = numberValue(request, "uncertainty", 0.5);
    const minimum = numberValue(request, "min_information_gain", 0.2);
    const budget = numberValue(request, "budget", Number.POSITIVE_INFINITY);
    const observations = (value(request, "observations", []) as Record<string, unknown>[]) ?? [];

    if (uncertainty < minimum) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "uncertainty_low", rationale: "uncertainty is low enough to decide without another look", confidence: 1 - uncertainty })];
    }
    if (observations.length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "no_observation", rationale: "no observation is available", confidence: 0.4 })];
    }
    const best = [...observations].sort((a, b) => {
      const score = (item: Record<string, unknown>) =>
        (Number(item.information_gain ?? 0) * uncertainty) / Math.max(Number(item.cost ?? 0), 0.001);
      return score(b) - score(a);
    })[0];
    const gain = Number(best.information_gain ?? 0) * uncertainty;
    const cost = Number(best.cost ?? 0);
    if (gain < minimum || cost > budget) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "observation_not_worth_it", rationale: "the available observation costs more than it is expected to resolve", confidence: 0.5 })];
    }
    const id = String(best.id ?? "");
    return [makeDecision({ policy: this.name, verb: "observe", reasonCode: "observe_for_information", rationale: `take observation ${id || "?"} to reduce uncertainty`, confidence: Math.min(0.95, 0.5 + gain), intent: { capability: "observe", args: { id } }, score: gain, actionId: id })];
  }
}
