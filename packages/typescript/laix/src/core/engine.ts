import type { ActionOption, Decision, DecisionRequest, Intent, Verb } from "./contracts.ts";

export interface DecisionProblem {
  subject: string;
  at: string;
  situation?: unknown;
  options: ActionOption[];
  signals?: unknown[];
  context?: unknown;
  attributes: Record<string, unknown>;
}

export interface Plan {
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

export interface DecisionEngine {
  solve(problem: DecisionProblem): Plan;
}

export function toProblem(request: DecisionRequest): DecisionProblem {
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

export class EnginePolicy {
  readonly name: string;
  readonly engine: DecisionEngine;

  constructor(engine: DecisionEngine, name = "engine.v1") {
    this.engine = engine;
    this.name = name;
  }

  decide(request: DecisionRequest): Decision[] {
    const plan = this.engine.solve(toProblem(request));
    return [
      {
        verb: plan.verb,
        confidence: plan.confidence,
        reasonCode: plan.reasonCode,
        rationale: plan.rationale,
        actionId: plan.actionId ?? null,
        intent: plan.intent ?? null,
        requiresApproval: plan.requiresApproval ?? false,
        reversible: plan.reversible ?? false,
        undoHint: plan.undoHint ?? null,
        score: plan.score ?? null,
        alternatives: plan.alternatives ?? [],
        attributes: { ...(request.attributes ?? {}), ...(plan.attributes ?? {}) },
        policyVersion: this.name,
      },
    ];
  }
}
