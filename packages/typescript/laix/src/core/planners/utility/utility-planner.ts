import type { ActionOption } from "../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../contract/planner.ts";
import { UtilityModel } from "./utility-model.ts";
import type { RiskAttitude } from "./utility-model.ts";

export { RISK_ATTITUDES, UtilityModel } from "./utility-model.ts";
export type { RiskAttitude, UtilityOptions, UtilityWeights } from "./utility-model.ts";

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

export function constraintBlocker(
  problem: PlannerInput,
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

export function approvalRequired(problem: PlannerInput): boolean {
  const situation = problem.situation as SituationLike | undefined;
  return Boolean(
    situation?.constraints?.some(
      (constraint) =>
        constraint.kind === "approval" && truthy(constraint.value),
    ),
  );
}

export class UtilityPlanner {
  readonly name = "utility.v1";
  readonly model: UtilityModel;

  constructor(model: UtilityModel = new UtilityModel()) {
    this.model = model;
  }

  solve(problem: PlannerInput): PlannerResult {
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
    problem: PlannerInput,
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

  private wait(reasonCode: string, rationale: string): PlannerResult {
    return { verb: "wait", confidence: 1.0, reasonCode, rationale, score: 0.0 };
  }
}
