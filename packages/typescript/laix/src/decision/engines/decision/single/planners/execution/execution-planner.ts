import type { ActionOption } from "../../../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../../../contract/planner.ts";
import {
  UtilityPlanner,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "../utility/utility-planner.ts";
import type { RiskAttitude } from "../utility/utility-planner.ts";

export interface ExecutionWeights {
  irreversible?: number;
  unknown?: number;
  approval?: number;
  recovery?: number;
}

export interface ExecutionEffect {
  unknownRisk: number;
  recoveryCost: number;
}

export interface ExecutionScore {
  utility: number;
  execution: number;
  total: number;
  irreversible: boolean;
  unknownRisk: number;
  recoveryCost: number;
  requiresApproval: boolean;
  receiptStatus: string | null;
  blocked: string | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function executionEffect(option: ActionOption): ExecutionEffect {
  const params = (option.params ?? {}) as Record<string, unknown>;
  const payload = (params.execution ?? params) as Record<string, unknown>;
  if (!payload || typeof payload !== "object") {
    return { unknownRisk: 0, recoveryCost: 0 };
  }
  const pick = (key: string): unknown =>
    payload[key] ?? (payload !== params ? params[key] : undefined);
  const unknown = Number(pick("unknown_risk") ?? 0);
  const recovery = Number(pick("recovery_cost") ?? 0);
  return {
    unknownRisk: clamp(Number.isNaN(unknown) ? 0 : unknown),
    recoveryCost: Math.max(0, Number.isNaN(recovery) ? 0 : recovery),
  };
}

export function receiptStatus(
  problem: PlannerInput,
  option: ActionOption,
): string | null {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const state = attributes.execution_state;
  if (state && typeof state === "object" && !Array.isArray(state)) {
    const value = (state as Record<string, unknown>)[option.id];
    return value === undefined || value === null ? null : String(value);
  }
  const receipts = attributes.execution_receipts;
  if (!Array.isArray(receipts)) return null;
  for (const receipt of receipts) {
    if (!receipt || typeof receipt !== "object") continue;
    const payload = receipt as Record<string, unknown>;
    const name = payload.actionName ?? payload.action_name;
    const status = payload.status;
    if ((name === option.id || name === option.name) && status !== undefined) {
      return String(status);
    }
  }
  return null;
}

export function executionScoreOption(
  option: ActionOption,
  model: UtilityModel,
  weights: Required<ExecutionWeights>,
  approval: boolean,
  receipt: string | null,
): ExecutionScore {
  const effect = executionEffect(option);
  const reversible = option.reversible ?? true;
  const irreversible = !reversible;
  let requiresApproval = approval || Boolean(option.requiresApproval || option.destructive);
  let unknownRisk = effect.unknownRisk;
  let recoveryCost = effect.recoveryCost;
  if (receipt === "unknown") unknownRisk = Math.max(unknownRisk, 1);
  if (["failed", "refused", "cancelled", "undone"].includes(receipt ?? "")) {
    recoveryCost = Math.max(recoveryCost, 1);
  }
  if (receipt === "pending") requiresApproval = true;
  const execution =
    -weights.irreversible * (irreversible ? 1 : 0) -
    weights.unknown * unknownRisk -
    weights.approval * (requiresApproval ? 1 : 0) -
    weights.recovery * recoveryCost;
  const utility = model.score(option);
  return {
    utility: round(utility),
    execution: round(execution),
    total: round(utility + execution),
    irreversible,
    unknownRisk,
    recoveryCost,
    requiresApproval,
    receiptStatus: receipt,
    blocked: null,
  };
}

interface Row {
  option: ActionOption;
  score: ExecutionScore;
  feasible: boolean;
  blocker: string | null;
}

export class ExecutionRiskPlanner {
  readonly name = "execution.v1";
  readonly model: UtilityModel;
  readonly weights: Required<ExecutionWeights>;
  private readonly utility: UtilityPlanner;

  constructor(model: UtilityModel = new UtilityModel(), weights: ExecutionWeights = {}) {
    this.model = model;
    this.weights = {
      irreversible: weights.irreversible ?? 0.35,
      unknown: weights.unknown ?? 0.5,
      approval: weights.approval ?? 0.15,
      recovery: weights.recovery ?? 0.25,
    };
    for (const [key, value] of Object.entries(this.weights)) {
      if (value < 0) throw new Error(`execution weight ${key} must not be negative`);
    }
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
    const options = [...(problem.options ?? [])];
    if (!options.length) {
      return this.wait("no_options", "there are no options to score");
    }
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const approval = approvalRequired(problem);
    const rows: Row[] = options.map((option) => {
      const score = executionScoreOption(
        option,
        model,
        this.weights,
        approval,
        receiptStatus(problem, option),
      );
      const blocker = constraintBlocker(problem, option);
      return {
        option,
        score,
        feasible: model.feasible(option) && blocker === null,
        blocker,
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      return this.wait("no_feasible_option", "every option is outside the hard limits");
    }
    feasible.sort((left, right) =>
      right.score.total !== left.score.total
        ? right.score.total - left.score.total
        : left.option.id < right.option.id
          ? -1
          : 1,
    );
    const best = feasible[0]!;
    const second = feasible[1]?.score.total;
    return {
      verb: best.option.verb,
      confidence: this.confidence(best.score.total, second),
      reasonCode: "execution_aware",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)} and execution cost ${best.score.execution >= 0 ? "+" : ""}${best.score.execution.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.option.requiresApproval || best.option.destructive || approval,
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        execution_score: best.score.execution,
        irreversible: best.score.irreversible,
        unknown_risk: best.score.unknownRisk,
        recovery_cost: best.score.recoveryCost,
        requires_approval: best.score.requiresApproval,
        receipt_status: best.score.receiptStatus,
      },
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

  private alternatives(rows: Row[], bestId: string): Array<Record<string, unknown>> {
    return rows
      .filter((row) => row.option.id !== bestId)
      .map((row) => ({
        action_id: row.option.id,
        verb: row.option.verb,
        name: row.option.name,
        utility: row.score.utility,
        execution: row.score.execution,
        total: row.score.total,
        rejected_because: !row.feasible
          ? row.blocker
            ? `blocked by ${row.blocker}`
            : "outside the hard limits"
          : "lower execution-adjusted score",
      }))
      .sort((left, right) =>
        Number(right.total) !== Number(left.total)
          ? Number(right.total) - Number(left.total)
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
