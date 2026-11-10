import type { PlannerInput, PlannerResult } from "../../../contract/planner.ts";
import { UtilityModel, UtilityPlanner } from "../utility/utility-planner.ts";

function risk(option: { params?: Record<string, unknown>; risk?: number }, key: string, fallback: number): number {
  const params = option.params ?? {};
  const rawBound = params.risk_bound ?? params.risk;
  const bound =
    rawBound && typeof rawBound === "object"
      ? (rawBound as Record<string, unknown>)
      : {};
  const value = bound[key] ?? params[key] ?? fallback;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? fallback : parsed;
}

export class RiskBoundedPlanner {
  readonly name = "risk_bounded.v1";
  readonly model: UtilityModel;
  readonly maxLoss: number;
  readonly penalty: number;
  private readonly utility: UtilityPlanner;

  constructor(
    model: UtilityModel = new UtilityModel(),
    options: { maxLoss?: number; penalty?: number } = {},
  ) {
    this.model = model;
    this.maxLoss = options.maxLoss ?? 0.5;
    this.penalty = options.penalty ?? 0;
    if (this.maxLoss < 0) throw new Error("maxLoss must not be negative");
    if (this.penalty < 0) throw new Error("penalty must not be negative");
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
    const options = [...(problem.options ?? [])];
    if (!options.length) return this.wait("no_options", "there are no options to score");
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const rows = options.map((option) => {
      const utility = model.score(option);
      const worst = risk(option, "worst_case_loss", option.risk ?? 0);
      const cvar = risk(option, "cvar_loss", worst);
      const total = Math.round((utility - this.penalty * Math.max(0, Math.min(1, cvar))) * 1e6) / 1e6;
      return {
        option,
        utility: Math.round(utility * 1e6) / 1e6,
        worst,
        cvar,
        total,
        feasible: model.feasible(option) && cvar <= this.maxLoss,
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      return this.wait("no_feasible_option", "every option exceeds the downside limit", {
        risk_limit: this.maxLoss,
      });
    }
    feasible.sort((left, right) =>
      right.total !== left.total
        ? right.total - left.total
        : left.option.id < right.option.id
          ? -1
          : 1,
    );
    const best = feasible[0]!;
    const second = feasible[1]?.total;
    return {
      verb: best.option.verb,
      confidence: this.confidence(best.total, second),
      reasonCode: "risk_bounded",
      rationale: `${best.option.id} keeps CVaR ${best.cvar.toFixed(3)} within ${this.maxLoss.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(best.option.requiresApproval),
      reversible: best.option.reversible ?? true,
      score: best.total,
      alternatives: rows
        .filter((row) => row.option.id !== best.option.id)
        .map((row) => ({
          action_id: row.option.id,
          verb: row.option.verb,
          name: row.option.name,
          utility: row.utility,
          total: row.total,
          cvar_loss: row.cvar,
          rejected_reason_code: row.feasible
            ? "lower_risk_adjusted_score"
            : "risk_limit",
        })),
      attributes: {
        risk_limit: this.maxLoss,
        worst_case_loss: best.worst,
        cvar_loss: best.cvar,
        utility: best.utility,
      },
    };
  }

  private confidence(best: number, second: number | undefined): number {
    if (second === undefined) return 1;
    const gap = Math.max(0, best - second);
    return Math.min(1, Math.max(0, 0.5 + 0.5 * (gap / Math.max(Math.abs(best), 1e-9))));
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
        (attributes.risk_attitude as "averse" | "neutral" | "seeking" | undefined) ??
        this.model.riskAttitude,
      maxRisk:
        attributes.max_risk === undefined
          ? this.model.maxRisk
          : Number(attributes.max_risk),
      maxCost:
        attributes.max_cost === undefined
          ? this.model.maxCost
          : Number(attributes.max_cost),
      maxLatencyMs:
        attributes.max_latency_ms === undefined
          ? this.model.maxLatencyMs
          : Number(attributes.max_latency_ms),
    });
  }

  private wait(
    reasonCode: string,
    rationale: string,
    attributes: Record<string, unknown> = {},
  ): PlannerResult {
    return {
      verb: "wait",
      confidence: 1,
      reasonCode,
      rationale,
      score: 0,
      attributes,
    };
  }
}
