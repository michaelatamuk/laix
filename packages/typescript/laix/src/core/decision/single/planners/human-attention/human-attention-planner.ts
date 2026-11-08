import type { ActionOption } from "../../../../contracts.ts";
import type { PlannerInput, PlannerResult } from "../../../../contract/planner.ts";
import {
  UtilityPlanner,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "../utility/utility-planner.ts";
import type { RiskAttitude } from "../utility/utility-planner.ts";
import { HumanAttentionBudget } from "./human-attention-budget.ts";

export { HumanAttentionBudget };

export interface HumanAttentionWeights {
  interrupt?: number;
  approval?: number;
  escalation?: number;
  exhausted?: number;
}

export interface HumanAttentionEffect {
  interruptCost: number;
  requiresApproval: boolean;
  escalates: boolean;
  interactive: boolean;
  approvalState: string | null;
}

export interface HumanAttentionScore {
  utility: number;
  human_attention: number;
  total: number;
  effect: HumanAttentionEffect;
  remaining: number;
  blocked: string | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function humanAttentionEffect(
  option: ActionOption,
  approval = false,
  approvalState: string | null = null,
): HumanAttentionEffect {
  const params = (option.params ?? {}) as Record<string, unknown>;
  const payload = (params.attention ?? params) as Record<string, unknown>;
  const source = payload && typeof payload === "object" ? payload : params;
  const rawInterrupt = Number(source.interrupt_cost ?? option.interruptCost ?? 0);
  let requiresApproval = Boolean(
    approval ||
      source.requires_approval ||
      option.requiresApproval ||
      option.destructive,
  );
  if (approvalState === "approved") requiresApproval = false;
  if (approvalState === "pending" || approvalState === "rejected") {
    requiresApproval = true;
  }
  const escalates = Boolean(source.escalates ?? option.verb === "escalate");
  return {
    interruptCost: clamp(Number.isNaN(rawInterrupt) ? 0 : rawInterrupt),
    requiresApproval,
    escalates,
    interactive: option.verb === "ask" || option.verb === "guide",
    approvalState,
  };
}

export function approvalState(
  problem: PlannerInput,
  option: ActionOption,
): string | null {
  const raw = (problem.attributes ?? {}).approvals;
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    const value = (raw as Record<string, unknown>)[option.id] ??
      (raw as Record<string, unknown>)[option.name];
    if (value === undefined || value === null) return null;
    if (typeof value === "boolean") return value ? "approved" : "rejected";
    return String(value);
  }
  if (Array.isArray(raw)) {
    for (const item of raw) {
      if (!item || typeof item !== "object") continue;
      const payload = item as Record<string, unknown>;
      const name = payload.actionId ?? payload.action_id ?? payload.actionName ??
        payload.action_name;
      let status = payload.status;
      if (status === undefined && "approved" in payload) {
        status = payload.approved ? "approved" : "rejected";
      }
      if ((name === option.id || name === option.name) && status !== undefined) {
        return String(status);
      }
    }
  }
  return null;
}

export function humanAttentionCost(effect: HumanAttentionEffect): number {
  return (
    effect.interruptCost +
    (effect.requiresApproval ? 0.5 : 0) +
    (effect.escalates ? 0.5 : 0) +
    (effect.interactive ? 0.5 : 0)
  );
}

export function remainingBudget(problem: PlannerInput): number {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const raw = attributes.human_attention_budget ?? 1.0;
  let base: number;
  if (raw instanceof HumanAttentionBudget) {
    base = raw.remaining();
  } else if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    const payload = raw as Record<string, unknown>;
    base = Number(payload.total ?? 1) - Number(payload.spent ?? 0);
  } else {
    base = Number(raw) - Number(attributes.human_attention_spent ?? 0);
  }
  const explicit = attributes.human_attention_remaining;
  const remaining = explicit === undefined ? base : Number(explicit);
  if (Number.isNaN(remaining)) return Math.max(0, base);
  return Math.max(0, remaining);
}

export function humanAttentionScoreOption(
  option: ActionOption,
  model: UtilityModel,
  weights: Required<HumanAttentionWeights>,
  remaining: number,
  approval: boolean,
  state: string | null,
): HumanAttentionScore {
  const effect = humanAttentionEffect(option, approval, state);
  const cost = humanAttentionCost(effect);
  const blocked =
    state === "rejected"
      ? "approval rejected"
      : cost > remaining
        ? "human attention budget exhausted"
        : null;
  const attention =
    -weights.interrupt * effect.interruptCost -
    weights.approval * (effect.requiresApproval ? 1 : 0) -
    weights.escalation * (effect.escalates ? 1 : 0) -
    weights.exhausted * (blocked ? 1 : 0);
  const utility = model.score(option);
  return {
    utility: round(utility),
    human_attention: round(attention),
    total: round(utility + attention),
    effect,
    remaining: Math.max(0, remaining - cost),
    blocked,
  };
}

interface Row {
  option: ActionOption;
  score: HumanAttentionScore;
  feasible: boolean;
  blocker: string | null;
}

export class HumanAttentionPlanner {
  readonly name = "human-attention.v1";
  readonly model: UtilityModel;
  readonly weights: Required<HumanAttentionWeights>;
  private readonly utility: UtilityPlanner;

  constructor(model: UtilityModel = new UtilityModel(), weights: HumanAttentionWeights = {}) {
    this.model = model;
    this.weights = {
      interrupt: weights.interrupt ?? 0.4,
      approval: weights.approval ?? 0.25,
      escalation: weights.escalation ?? 0.3,
      exhausted: weights.exhausted ?? 1.0,
    };
    for (const [key, value] of Object.entries(this.weights)) {
      if (value < 0) throw new Error(`attention weight ${key} must not be negative`);
    }
    this.utility = new UtilityPlanner(model);
  }

  solve(problem: PlannerInput): PlannerResult {
    const options = [...(problem.options ?? [])];
    if (!options.length) {
      return this.wait("no_options", "there are no options to score");
    }
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const remaining = remainingBudget(problem);
    const approval = approvalRequired(problem);
    const rows: Row[] = options.map((option) => {
      const score = humanAttentionScoreOption(
        option,
        model,
        this.weights,
        remaining,
        approval,
        approvalState(problem, option),
      );
      const blocker = constraintBlocker(problem, option);
      return {
        option,
        score,
        feasible:
          model.feasible(option) && blocker === null && score.blocked === null,
        blocker: score.blocked ?? blocker,
      };
    });
    const feasible = rows.filter((row) => row.feasible);
    if (!feasible.length) {
      if (rows.some((row) => row.blocker === "approval rejected")) {
        return this.wait(
          "approval_rejected",
          "every remaining option was rejected or needs more attention",
        );
      }
      return this.wait(
        "human_attention_budget_exhausted",
        "every option needs more human attention than is left",
      );
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
      reasonCode: "human_attention_aware",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)} and attention cost ${best.score.human_attention >= 0 ? "+" : ""}${best.score.human_attention.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: best.score.effect.requiresApproval,
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        human_attention_score: best.score.human_attention,
        human_attention_cost: humanAttentionCost(best.score.effect),
        human_attention_remaining: best.score.remaining,
        human_attention_budget_blocked: best.score.blocked,
        approval_state: best.score.effect.approvalState,
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
        human_attention: row.score.human_attention,
        total: row.score.total,
        rejected_because: !row.feasible
          ? row.blocker
            ? `blocked by ${row.blocker}`
            : "outside the hard limits"
          : "lower attention-adjusted score",
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
