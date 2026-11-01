import type { Arm, UCBBandit } from "../outcome.ts";
import type { Decision, DecisionRequest, Outcome } from "../contracts.ts";
import { makeDecision, numberValue, value } from "./support.ts";

function toArm(item: Arm | Record<string, unknown>): Arm {
  if ("id" in item && ("priorMean" in item || "priorMean" in item || "cost" in item || "risk" in item)) {
    return item as Arm;
  }
  const raw = item as Record<string, unknown>;
  return {
    id: String(raw.id ?? ""),
    priorMean: Number(raw.prior_mean ?? raw.priorMean ?? 0.5),
    priorWeight: Number(raw.prior_weight ?? raw.priorWeight ?? 1),
    cost: Number(raw.cost ?? 0),
    risk: Number(raw.risk ?? 0),
  };
}

export class BanditPolicy {
  name = "bandit.v1";
  version = "0.6.1";
  bandit: UCBBandit;
  maxRisk: number;
  budget: number;

  constructor(bandit: UCBBandit, options: { maxRisk?: number; budget?: number } = {}) {
    this.bandit = bandit;
    this.maxRisk = options.maxRisk ?? 1;
    this.budget = options.budget ?? Number.POSITIVE_INFINITY;
  }

  decide(request: DecisionRequest): Decision[] {
    for (const item of (value(request, "arms", []) as Array<Arm | Record<string, unknown>>) ?? []) {
      this.bandit.add(toArm(item));
    }
    if (this.bandit.arms().length === 0) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "no_arms", rationale: "the learner has no arm to choose", confidence: 0.5 })];
    }
    const chosen = this.bandit.choose({
      maxRisk: numberValue(request, "max_risk", this.maxRisk),
      budget: numberValue(request, "budget", this.budget),
      exclude: (value(request, "exclude", []) as string[]) ?? [],
    });
    if (!chosen) {
      return [makeDecision({ policy: this.name, verb: "wait", reasonCode: "no_arm_within_limits", rationale: "every arm breaks the risk or budget limit", confidence: 0.7 })];
    }
    const mean = this.bandit.mean(chosen.id);
    return [makeDecision({
      policy: this.name,
      verb: "act",
      reasonCode: "bandit_choice",
      rationale: `choose arm ${chosen.id} with learned reward ${mean.toFixed(2)}`,
      confidence: Math.min(0.98, 0.5 + mean * 0.4),
      intent: { capability: "act", args: { arm: chosen.id } },
      score: mean,
      requiresApproval: Boolean(value(request, "requires_approval", false)),
      actionId: chosen.id,
    })];
  }

  record(armId: string, reward: number): Arm {
    return this.bandit.update(armId, reward);
  }

  learn(outcomes: Outcome[], armOf: (decisionId: string) => string): number {
    return this.bandit.learn(outcomes, armOf);
  }
}
