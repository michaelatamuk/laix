import type { ActionOption } from "./contracts.ts";
import type { DecisionProblem, Plan } from "./engine.ts";

export const RISK_ATTITUDES = ["neutral", "averse", "seeking"] as const;
export type RiskAttitude = (typeof RISK_ATTITUDES)[number];

export interface UtilityWeights {
  benefit?: number;
  cost?: number;
  risk?: number;
  interruption?: number;
  latency?: number;
}

export interface UtilityOptions {
  weights?: UtilityWeights;
  riskAttitude?: RiskAttitude;
  maxRisk?: number;
  maxCost?: number | null;
  maxLatencyMs?: number | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

interface ConstraintLike {
  id?: string;
  kind?: string;
  value?: unknown;
  hard?: boolean;
}

interface SituationLike {
  constraints?: ConstraintLike[];
}

function truthy(value: unknown): boolean {
  if (typeof value === "string") {
    return ["1", "true", "yes", "required", "always", "blocked", "on"].includes(
      value.trim().toLowerCase(),
    );
  }
  return Boolean(value);
}

function limit(kind: string, value: unknown): number | null {
  let resolved = value;
  if (resolved && typeof resolved === "object" && !Array.isArray(resolved)) {
    const payload = resolved as Record<string, unknown>;
    resolved = payload.max ?? payload.value;
  }
  if (typeof resolved === "boolean" || resolved === null || resolved === undefined) {
    return null;
  }
  const numeric = Number(resolved);
  if (Number.isNaN(numeric)) return null;
  if (kind === "interruption") return numeric <= 1 ? numeric : numeric / 100;
  return numeric;
}

function constraintBlocker(
  problem: DecisionProblem,
  option: ActionOption,
): string | null {
  const situation = problem.situation as SituationLike | undefined;
  if (!situation?.constraints?.length) return null;
  const amounts: Record<string, number> = {
    risk: option.risk ?? 0,
    cost: option.cost ?? 0,
    budget: option.cost ?? 0,
    latency: option.latencyMs ?? 0,
    interruption: option.interruptCost ?? 0,
  };
  for (const constraint of situation.constraints) {
    if (!constraint.hard) continue;
    const kind = constraint.kind ?? "";
    if (kind === "safety") {
      if (truthy(constraint.value)) return "safety";
      continue;
    }
    if (!(kind in amounts)) continue;
    const max = limit(kind, constraint.value);
    if (max !== null && amounts[kind]! > max) {
      return `${kind}:${constraint.id ?? kind}`;
    }
  }
  return null;
}

function approvalRequired(problem: DecisionProblem): boolean {
  const situation = problem.situation as SituationLike | undefined;
  return Boolean(
    situation?.constraints?.some(
      (constraint) =>
        constraint.kind === "approval" && truthy(constraint.value),
    ),
  );
}

export class UtilityModel {
  readonly weights: Required<UtilityWeights>;
  readonly riskAttitude: RiskAttitude;
  readonly maxRisk: number;
  readonly maxCost: number | null;
  readonly maxLatencyMs: number | null;

  constructor(options: UtilityOptions = {}) {
    this.weights = {
      benefit: options.weights?.benefit ?? 1.0,
      cost: options.weights?.cost ?? 0.25,
      risk: options.weights?.risk ?? 0.25,
      interruption: options.weights?.interruption ?? 0.15,
      latency: options.weights?.latency ?? 0.0,
    };
    for (const [name, value] of Object.entries(this.weights)) {
      if (value < 0) throw new Error(`utility weight ${name} must not be negative`);
    }
    this.riskAttitude = options.riskAttitude ?? "neutral";
    if (!RISK_ATTITUDES.includes(this.riskAttitude)) {
      throw new Error(`unknown risk attitude: ${this.riskAttitude}`);
    }
    this.maxRisk = options.maxRisk ?? 1.0;
    if (this.maxRisk < 0 || this.maxRisk > 1) {
      throw new Error("maxRisk must be between zero and one");
    }
    this.maxCost = options.maxCost ?? null;
    this.maxLatencyMs = options.maxLatencyMs ?? null;
  }

  feasible(option: ActionOption): boolean {
    const risk = option.risk ?? 0;
    if (risk > this.maxRisk) return false;
    if (this.maxCost !== null && (option.cost ?? 0) > this.maxCost) return false;
    if (this.maxLatencyMs !== null && (option.latencyMs ?? 0) > this.maxLatencyMs) {
      return false;
    }
    return true;
  }

  score(option: ActionOption): number {
    let risk = option.risk ?? 0;
    if (this.riskAttitude === "averse") risk *= 1 + risk;
    if (this.riskAttitude === "seeking") risk *= 1 - 0.5 * risk;
    return round(
      this.weights.benefit * (option.expectedBenefit ?? 0.5) -
        this.weights.cost * (option.cost ?? 0) -
        this.weights.risk * risk -
        this.weights.interruption * (option.interruptCost ?? 0) -
        this.weights.latency * (option.latencyMs ?? 0),
    );
  }
}

export class UtilityEngine {
  readonly name = "utility.v1";
  readonly model: UtilityModel;

  constructor(model: UtilityModel = new UtilityModel()) {
    this.model = model;
  }

  solve(problem: DecisionProblem): Plan {
    const options = [...(problem.options ?? [])];
    if (!options.length) return this.wait("no_options", "there are no options to score");

    const model = this.modelFor(problem.attributes ?? {});
    const feasible = options.filter(
      (option) =>
        model.feasible(option) && constraintBlocker(problem, option) === null,
    );
    if (!feasible.length) {
      return this.wait("no_feasible_option", "every option is outside the hard limits");
    }

    const scored = feasible
      .map((option) => ({ score: model.score(option), option }))
      .sort((left, right) =>
        right.score !== left.score
          ? right.score - left.score
          : left.option.id < right.option.id
            ? -1
            : 1,
      );
    const best = scored[0]!;
    const second = scored[1]?.score;
    return {
      verb: best.option.verb,
      confidence: this.confidence(best.score, second),
      reasonCode: "expected_utility",
      rationale: `${best.option.id} has the highest expected utility ${best.score.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.option.requiresApproval ||
          best.option.destructive ||
          approvalRequired(problem),
      ),
      reversible: best.option.reversible ?? true,
      score: best.score,
      alternatives: this.alternatives(problem, options, model, best.option),
      attributes: { utility: best.score, risk_attitude: model.riskAttitude },
    };
  }

  private modelFor(attributes: Record<string, unknown>): UtilityModel {
    if (
      attributes.max_risk === undefined &&
      attributes.max_cost === undefined &&
      attributes.max_latency_ms === undefined &&
      attributes.risk_attitude === undefined
    ) {
      return this.model;
    }
    return new UtilityModel({
      weights: this.model.weights,
      riskAttitude:
        (attributes.risk_attitude as RiskAttitude | undefined) ?? this.model.riskAttitude,
      maxRisk:
        attributes.max_risk === undefined ? this.model.maxRisk : Number(attributes.max_risk),
      maxCost:
        attributes.max_cost === undefined ? this.model.maxCost : Number(attributes.max_cost),
      maxLatencyMs:
        attributes.max_latency_ms === undefined
          ? this.model.maxLatencyMs
          : Number(attributes.max_latency_ms),
    });
  }

  private alternatives(
    problem: DecisionProblem,
    options: ActionOption[],
    model: UtilityModel,
    best: ActionOption,
  ): Array<Record<string, unknown>> {
    return options
      .filter((option) => option.id !== best.id)
      .map((option) => {
        const blocker = constraintBlocker(problem, option);
        return {
          action_id: option.id,
          verb: option.verb,
          name: option.name,
          utility: model.score(option),
          rejected_because: !model.feasible(option)
            ? "outside the hard limits"
            : blocker !== null
              ? `blocked by ${blocker}`
              : "lower expected utility",
        };
      })
      .sort((left, right) =>
        Number(right.utility) !== Number(left.utility)
          ? Number(right.utility) - Number(left.utility)
          : String(left.action_id) < String(right.action_id)
            ? -1
            : 1,
      );
  }

  private confidence(best: number, second: number | undefined): number {
    if (second === undefined) return 1.0;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
  }

  private wait(reasonCode: string, rationale: string): Plan {
    return { verb: "wait", confidence: 1.0, reasonCode, rationale, score: 0.0 };
  }
}
