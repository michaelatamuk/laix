import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

export class EscalationPolicy {
  name = "escalation.v1";
  version = "0.8.0";

  decide(request: DecisionRequest): Decision[] {
    if (Boolean(value(request, "resolved", false))) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "resolved", rationale: "the situation is resolved; no escalation is needed", confidence: 1 })];
    }
    const severity = numberValue(request, "severity", 0);
    const threshold = numberValue(request, "severity_threshold", 0.8);
    const attempts = Math.trunc(numberValue(request, "attempts", 0));
    const maxAttempts = Math.trunc(numberValue(request, "max_attempts", 3));
    const confidence = numberValue(request, "confidence", 1);
    const minConfidence = numberValue(request, "min_confidence", 0.5);
    const slaBreached = Boolean(value(request, "sla_breached", false));

    const reasons: string[] = [];
    if (severity >= threshold) reasons.push(`severity ${severity.toFixed(2)} reached ${threshold.toFixed(2)}`);
    if (attempts >= maxAttempts) reasons.push(`attempts ${attempts} reached ${maxAttempts}`);
    if (confidence < minConfidence) reasons.push(`confidence ${confidence.toFixed(2)} is below ${minConfidence.toFixed(2)}`);
    if (slaBreached) reasons.push("the service level is breached");

    if (reasons.length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "within_limits", rationale: "severity, attempts and confidence are still within limits", confidence })];
    }
    const target = String(value(request, "target", "") ?? "");
    const rationale = reasons.join("; ");
    if (!target) {
      return [makeDecision({ policy: this.name, verb: "ask", reasonCode: "target_required", rationale: `${rationale}; no escalation target is known`, confidence: 0.7 })];
    }
    return [makeDecision({ policy: this.name, verb: "escalate", reasonCode: "escalate_to_target", rationale: `${rationale}; hand over to ${target}`, confidence: Math.min(0.98, Math.max(severity, 1 - confidence)), escalation: { target, reason: rationale }, score: severity, actionId: target })];
  }
}
