import type { Decision } from "./contracts.ts";

export type AttributeValue = string | number | boolean;

/**
 * Map one decision onto stable OpenTelemetry attribute names.
 *
 * The package does not depend on an OpenTelemetry SDK. Attach the result to
 * the host's own span, log or metric.
 */
export function decisionAttributes(
  decision: Decision,
): Record<string, AttributeValue> {
  const attributes: Record<string, AttributeValue> = {
    "laix.verb": decision.verb,
    "laix.reason_code": decision.reasonCode,
    "laix.confidence": decision.confidence,
    "laix.approval.required": decision.requiresApproval ?? false,
    "laix.reversible": decision.reversible ?? false,
    "laix.status": decision.status ?? "final",
    "laix.target": decision.target ?? "one",
    "laix.calibrated": decision.calibrated ?? false,
  };
  const optional: Record<string, string | null | undefined> = {
    "laix.decision.id": decision.decisionId,
    "laix.trace.id": decision.traceId,
    "laix.situation.id": decision.situationId,
    "laix.action.id": decision.actionId,
    "laix.policy.version": decision.policyVersion,
    "laix.confidence.source": decision.confidenceSource,
    "laix.stream.id": decision.streamId,
    "laix.supersedes": decision.supersedes,
    "laix.event.time": decision.eventTime,
  };
  for (const [name, value] of Object.entries(optional)) {
    if (value !== null && value !== undefined && value !== "") {
      attributes[name] = value;
    }
  }
  if (decision.score !== null && decision.score !== undefined) {
    attributes["laix.score"] = decision.score;
  }
  if (decision.revision) {
    attributes["laix.revision"] = decision.revision;
  }
  return attributes;
}
