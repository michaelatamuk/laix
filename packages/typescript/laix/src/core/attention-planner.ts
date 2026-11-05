import type { ActionOption } from "./contracts.ts";
import type { DecisionProblem, Plan } from "./engine.ts";
import {
  UtilityEngine,
  UtilityModel,
  approvalRequired,
  constraintBlocker,
} from "./utility.ts";
import type { RiskAttitude } from "./utility.ts";

export interface AttentionWeights {
  interrupt?: number;
  approval?: number;
  escalation?: number;
  exhausted?: number;
}

export interface AttentionEffect {
  interruptCost: number;
  requiresApproval: boolean;
  escalates: boolean;
  interactive: boolean;
}

export interface AttentionScore {
  utility: number;
  attention: number;
  total: number;
  effect: AttentionEffect;
  remaining: number;
  blocked: string | null;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function clamp(value: number): number {
  return Math.min(1, Math.max(0, value));
}

export function attentionEffect(
  option: ActionOption,
  approval = false,
): AttentionEffect {
  const params = (option.params ?? {}) as Record<string, unknown>;
  const payload = (params.attention ?? params) as Record<string, unknown>;
  const source = payload && typeof payload === "object" ? payload : params;
  const rawInterrupt = Number(source.interrupt_cost ?? option.interruptCost ?? 0);
  const requiresApproval = Boolean(
    approval ||
      source.requires_approval ||
      option.requiresApproval ||
      option.destructive,
  );
  const escalates = Boolean(source.escalates ?? option.verb === "escalate");
  return {
    interruptCost: clamp(Number.isNaN(rawInterrupt) ? 0 : rawInterrupt),
    requiresApproval,
    escalates,
    interactive: option.verb === "ask" || option.verb === "guide",
  };
}

export function attentionCost(effect: AttentionEffect): number {
  return (
    effect.interruptCost +
    (effect.requiresApproval ? 0.5 : 0) +
    (effect.escalates ? 0.5 : 0) +
    (effect.interactive ? 0.5 : 0)
  );
}

function remainingBudget(problem: DecisionProblem): number {
  const attributes = (problem.attributes ?? {}) as Record<string, unknown>;
  const budget = Number(attributes.attention_budget ?? 1.0);
  const spent = Number(attributes.attention_spent ?? 0.0);
  const explicit = attributes.attention_remaining;
  const remaining =
    explicit === undefined ? budget - spent : Number(explicit);
  if (Number.isNaN(remaining)) return Math.max(0, budget - spent);
  return Math.max(0, remaining);
}

function scoreOption(
  option: ActionOption,
  model: UtilityModel,
  weights: Required<AttentionWeights>,
  remaining: number,
  approval: boolean,
): AttentionScore {
  const effect = attentionEffect(option, approval);
  const cost = attentionCost(effect);
  const blocked = cost > remaining ? "attention budget exhausted" : null;
  const attention =
    -weights.interrupt * effect.interruptCost -
    weights.approval * (effect.requiresApproval ? 1 : 0) -
    weights.escalation * (effect.escalates ? 1 : 0) -
    weights.exhausted * (blocked ? 1 : 0);
  const utility = model.score(option);
  return {
    utility: round(utility),
    attention: round(attention),
    total: round(utility + attention),
    effect,
    remaining: Math.max(0, remaining - cost),
    blocked,
  };
}

interface Row {
  option: ActionOption;
  score: AttentionScore;
  feasible: boolean;
  blocker: string | null;
}

export class AttentionAwareEngine {
  readonly name = "attention.v1";
  readonly model: UtilityModel;
  readonly weights: Required<AttentionWeights>;
  private readonly utility: UtilityEngine;

  constructor(model: UtilityModel = new UtilityModel(), weights: AttentionWeights = {}) {
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
    this.utility = new UtilityEngine(model);
  }

  solve(problem: DecisionProblem): Plan {
    const options = [...(problem.options ?? [])];
    if (!options.length) {
      return this.wait("no_options", "there are no options to score");
    }
    const model = this.modelFor((problem.attributes ?? {}) as Record<string, unknown>);
    const remaining = remainingBudget(problem);
    const approval = approvalRequired(problem);
    const rows: Row[] = options.map((option) => {
      const score = scoreOption(option, model, this.weights, remaining, approval);
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
      return this.wait(
        "attention_budget_exhausted",
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
      reasonCode: "attention_aware",
      rationale: `${best.option.id} balances utility ${best.score.utility.toFixed(3)} and attention cost ${best.score.attention >= 0 ? "+" : ""}${best.score.attention.toFixed(3)}`,
      actionId: best.option.id,
      requiresApproval: Boolean(
        best.option.requiresApproval || best.option.destructive || approval,
      ),
      reversible: best.option.reversible ?? true,
      score: best.score.total,
      alternatives: this.alternatives(rows, best.option.id),
      attributes: {
        utility: best.score.utility,
        attention_score: best.score.attention,
        attention_cost: attentionCost(best.score.effect),
        attention_remaining: best.score.remaining,
        attention_budget_blocked: best.score.blocked,
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
        attention: row.score.attention,
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

  private wait(reasonCode: string, rationale: string): Plan {
    return { verb: "wait", confidence: 1.0, reasonCode, rationale, score: 0.0 };
  }
}
