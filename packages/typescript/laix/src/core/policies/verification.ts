import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class VerificationPolicy {
  name = "verification.v1";
  version = "0.7.0";

  decide(request: DecisionRequest): Decision[] {
    if (Boolean(value(request, "verified", false))) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "already_verified", rationale: "the outcome is already confirmed", confidence: 1 })];
    }
    const confidence = numberValue(request, "confidence", 0.5);
    const required = numberValue(request, "required_confidence", 0.8);
    const due = value(request, "verification_due", true) !== false;
    const budget = numberValue(request, "budget", Number.POSITIVE_INFINITY);
    const checks = (value(request, "checks", []) as Record<string, unknown>[]) ?? [];
    const target = String(value(request, "escalation_target", "human") ?? "human");

    if (!due && confidence >= required) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "verification_not_needed", rationale: `confidence ${confidence.toFixed(2)} meets the requirement ${required.toFixed(2)}`, confidence })];
    }
    if (checks.length === 0) {
      return [makeDecision({ policy: this.name, verb: "escalate", reasonCode: "no_verification_path", rationale: "no check can confirm the outcome; ask a person", confidence: 0.6, escalation: { target, reason: "no verification path" } })];
    }
    const affordable = checks.filter((item) => Number(item.cost ?? 0) <= budget);
    if (affordable.length === 0) {
      return [makeDecision({ policy: this.name, verb: "escalate", reasonCode: "no_verification_budget", rationale: "every check costs more than the verification budget", confidence: 0.6, escalation: { target, reason: "verification budget exhausted" } })];
    }
    const gainOf = (item: Record<string, unknown>) => Number(item.confidence_gain ?? item.information_gain ?? 0);
    const best = [...affordable].sort((a, b) => gainOf(b) / Math.max(Number(b.cost ?? 0), 0.001) - gainOf(a) / Math.max(Number(a.cost ?? 0), 0.001))[0];
    const gain = gainOf(best);
    if (gain <= 0) {
      return [makeDecision({ policy: this.name, verb: "escalate", reasonCode: "no_verification_path", rationale: "no available check would raise confidence", confidence: 0.6, escalation: { target, reason: "no useful verification path" } })];
    }
    const id = String(best.id ?? "");
    return [makeDecision({ policy: this.name, verb: "verify", reasonCode: "verify_outcome", rationale: `run check ${id || "?"} to confirm the outcome`, confidence: Math.min(0.95, confidence + gain), intent: { capability: "verify", args: { id } }, score: gain, actionId: id })];
  }
}
