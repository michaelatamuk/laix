import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class PreferenceElicitationPolicy {
  name = "preference-elicitation.v1";
  version = "1.0";

  decide(request: DecisionRequest): Decision[] {
    const uncertainty = numberValue(request, "uncertainty", 0.5);
    const threshold = numberValue(request, "uncertainty_threshold", 0.2);
    const questions = (value(request, "questions", []) as Record<string, unknown>[]) ?? [];

    if (uncertainty <= threshold) {
      return [makeDecision({ policy: this.name, verb: "act", reasonCode: "preference_known", rationale: "uncertainty is low enough to choose without another question", confidence: 1 - uncertainty })];
    }
    if (questions.length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "no_question", rationale: "no useful question is available", confidence: 0.5 })];
    }
    const best = [...questions].sort((a, b) => {
      const score = (item: Record<string, unknown>) => Number(item.information_gain ?? 0) / Math.max(Number(item.cost ?? 0), 0.001);
      return score(b) - score(a);
    })[0];
    const gain = Number(best.information_gain ?? 0);
    const id = String(best.id ?? "");
    return [makeDecision({ policy: this.name, verb: "ask", reasonCode: "ask_preference", rationale: `ask ${id || "?"} to reduce preference uncertainty`, confidence: Math.min(0.95, 0.5 + gain), intent: { capability: "ask_question", args: { id } }, score: gain, actionId: id })];
  }
}
