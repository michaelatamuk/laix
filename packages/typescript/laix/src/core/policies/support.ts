import type { Decision, DecisionRequest, Intent } from "../contracts.ts";
import { clamp } from "../contracts.ts";

export function value(request: DecisionRequest, key: string, fallback: unknown = undefined): unknown {
  return request.attributes?.[key] ?? fallback;
}

export function numberValue(request: DecisionRequest, key: string, fallback: number): number {
  const raw = value(request, key, fallback);
  const parsed = typeof raw === "number" ? raw : Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export interface DecisionInput {
  policy: string;
  verb: Decision["verb"];
  reasonCode: string;
  rationale: string;
  confidence: number;
  intent?: Intent | null;
  escalation?: Decision["escalation"];
  score?: number | null;
  requiresApproval?: boolean;
  actionId?: string | null;
}

export function makeDecision(input: DecisionInput): Decision {
  return {
    verb: input.verb,
    confidence: clamp(input.confidence),
    reasonCode: input.reasonCode,
    rationale: input.rationale,
    policyVersion: input.policy,
    actionId: input.actionId ?? null,
    requiresApproval: input.requiresApproval ?? false,
    score: input.score ?? null,
    intent: input.intent ?? null,
    escalation: input.escalation ?? null,
    deliver: true,
    record: true,
  };
}
