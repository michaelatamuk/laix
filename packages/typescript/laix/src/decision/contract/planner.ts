import type { ActionOption, Decision, DecisionRequest, Intent, Verb } from "../contracts.ts";

export interface PlannerInput {
  subject: string;
  at: string;
  situation?: unknown;
  options: ActionOption[];
  signals?: unknown[];
  context?: unknown;
  attributes: Record<string, unknown>;
}

export interface PlannerResult {
  verb: Verb;
  confidence: number;
  reasonCode: string;
  rationale: string;
  actionId?: string | null;
  intent?: Intent | null;
  requiresApproval?: boolean;
  reversible?: boolean;
  undoHint?: string | null;
  score?: number | null;
  alternatives?: Array<Record<string, unknown>>;
  attributes?: Record<string, unknown>;
}

export interface Planner {
  solve(problem: PlannerInput): PlannerResult;
}

export function toPlannerInput(request: DecisionRequest): PlannerInput {
  return {
    subject: request.subject,
    at: request.at,
    situation: request.situation,
    options: request.options ?? [],
    signals: request.signals,
    context: request.context,
    attributes: { ...(request.attributes ?? {}) },
  };
}

export function toDecision(
  plannerResult: PlannerResult,
  request: DecisionRequest,
  options: { decisionId?: string; traceId?: string; policyVersion?: string } = {},
): Decision {
  return {
    verb: plannerResult.verb,
    confidence: plannerResult.confidence,
    reasonCode: plannerResult.reasonCode,
    rationale: plannerResult.rationale,
    decisionId: options.decisionId ?? "",
    traceId: options.traceId ?? "",
    actionId: plannerResult.actionId ?? null,
    intent: plannerResult.intent ?? null,
    requiresApproval: plannerResult.requiresApproval ?? false,
    reversible: plannerResult.reversible ?? false,
    undoHint: plannerResult.undoHint ?? null,
    score: plannerResult.score ?? null,
    alternatives: plannerResult.alternatives ?? [],
    attributes: { ...(request.attributes ?? {}), ...(plannerResult.attributes ?? {}) },
    policyVersion: options.policyVersion ?? "planner.v1",
  };
}

export class PlannerPolicy {
  readonly name: string;
  readonly planner: Planner;

  constructor(planner: Planner, name = "planner.v1") {
    this.planner = planner;
    this.name = name;
  }

  decide(request: DecisionRequest): Decision[] {
    const plan = this.planner.solve(toPlannerInput(request));
    return [toDecision(plan, request, { policyVersion: this.name })];
  }
}
