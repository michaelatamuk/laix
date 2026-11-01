import type { Outcome } from "./contracts.ts";
import { clamp } from "./contracts.ts";

export function rewardForLabel(label: string): number | null {
  return ({ helped: 1, neutral: 0.5, hurt: 0 } as Record<string, number>)[(label ?? "").trim().toLowerCase()] ?? null;
}

export interface OutcomeStore {
  add(outcome: Outcome): Outcome;
  forDecision(decisionId: string): Outcome[];
  all(): Outcome[];
  summary(): Record<string, unknown>;
}

export class OutcomeLedger implements OutcomeStore {
  records: Outcome[] = [];
  tolerance = 0.05;

  add(outcome: Outcome): Outcome {
    this.records.push(outcome);
    return outcome;
  }

  forDecision(decisionId: string): Outcome[] {
    return this.records.filter((item) => item.decisionId === decisionId);
  }

  all(): Outcome[] {
    return [...this.records];
  }

  summary(): Record<string, unknown> {
    const attributed = this.records.filter((item) => item.attributed);
    const helped = attributed.filter((item) => item.label === "helped");
    const hurt = attributed.filter((item) => item.label === "hurt");
    const gains = attributed.map((item) => (item.direction === "lower-better" ? -item.delta : item.delta));
    return {
      measured: this.records.length,
      attributed: attributed.length,
      attributionCoverage: Number((attributed.length / Math.max(1, this.records.length)).toFixed(3)),
      helped: helped.length,
      neutral: attributed.filter((item) => item.label === "neutral").length,
      hurt: hurt.length,
      meanGain: gains.length ? Number((gains.reduce((sum, item) => sum + item, 0) / gains.length).toFixed(6)) : 0,
      precision: Number((helped.length / Math.max(1, attributed.length)).toFixed(3)),
    };
  }

  byMetric(): Record<string, Record<string, number>> {
    const rows: Record<string, Record<string, number>> = {};
    for (const item of this.records) {
      const bucket = rows[item.metric] ?? { measured: 0, attributed: 0, helped: 0, hurt: 0, gain: 0 };
      bucket.measured += 1;
      if (item.attributed) {
        bucket.attributed += 1;
        bucket.helped += item.label === "helped" ? 1 : 0;
        bucket.hurt += item.label === "hurt" ? 1 : 0;
        bucket.gain += item.direction === "lower-better" ? -item.delta : item.delta;
      }
      rows[item.metric] = bucket;
    }
    for (const value of Object.values(rows)) value.gain = Number(value.gain.toFixed(6));
    return rows;
  }

  toDict(): Record<string, unknown> {
    return { tolerance: this.tolerance, records: [...this.records], summary: this.summary() };
  }
}

export interface Arm {
  id: string;
  priorMean?: number;
  priorWeight?: number;
  cost?: number;
  risk?: number;
}

export class UCBBandit {
  exploration: number;
  private armsById = new Map<string, Required<Arm>>();
  private pullsById = new Map<string, number>();
  private rewardsById = new Map<string, number>();

  constructor(arms: Arm[] = [], exploration = 1.4) {
    this.exploration = Math.max(0, exploration);
    for (const arm of arms) this.add(arm);
  }

  add(arm: Arm): void {
    const name = arm.id.trim();
    if (!name) throw new Error("arm id is required");
    this.armsById.set(name, {
      id: name,
      priorMean: clamp(arm.priorMean ?? 0.5),
      priorWeight: Math.max(0, arm.priorWeight ?? 1),
      cost: arm.cost ?? 0,
      risk: arm.risk ?? 0,
    });
    if (!this.pullsById.has(name)) this.pullsById.set(name, 0);
    if (!this.rewardsById.has(name)) this.rewardsById.set(name, 0);
  }

  arms(): Required<Arm>[] {
    return [...this.armsById.values()];
  }

  private get(armId: string): Required<Arm> {
    const arm = this.armsById.get(armId);
    if (!arm) throw new Error(`unknown arm '${armId}'`);
    return arm;
  }

  update(armId: string, reward: number): Required<Arm> {
    this.get(armId);
    this.pullsById.set(armId, (this.pullsById.get(armId) ?? 0) + 1);
    this.rewardsById.set(armId, (this.rewardsById.get(armId) ?? 0) + clamp(reward));
    return this.get(armId);
  }

  learn(outcomes: Outcome[], armOf: (decisionId: string) => string): number {
    let used = 0;
    for (const outcome of outcomes) {
      const reward = rewardForLabel(outcome.label);
      if (reward === null) continue;
      this.update(armOf(outcome.decisionId), reward);
      used += 1;
    }
    return used;
  }

  pulls(armId: string): number {
    this.get(armId);
    return this.pullsById.get(armId) ?? 0;
  }

  mean(armId: string): number {
    const arm = this.get(armId);
    const pulls = this.pullsById.get(armId) ?? 0;
    return clamp(((arm.priorMean ?? 0.5) * (arm.priorWeight ?? 1) + (this.rewardsById.get(armId) ?? 0)) / Math.max((arm.priorWeight ?? 1) + pulls, 1e-9));
  }

  score(armId: string): number {
    this.get(armId);
    const pulls = this.pullsById.get(armId) ?? 0;
    if (pulls === 0) return Number.POSITIVE_INFINITY;
    const total = [...this.pullsById.values()].reduce((sum, item) => sum + item, 0);
    return this.mean(armId) + this.exploration * Math.sqrt(Math.log(total + 1) / pulls);
  }

  choose(options: { maxRisk?: number; budget?: number; exclude?: string[] } = {}): Required<Arm> | null {
    const maxRisk = options.maxRisk ?? 1;
    const budget = options.budget ?? Number.POSITIVE_INFINITY;
    const blocked = new Set(options.exclude ?? []);
    let best: Required<Arm> | null = null;
    let bestScore = Number.NEGATIVE_INFINITY;
    for (const arm of this.armsById.values()) {
      if (blocked.has(arm.id) || (arm.risk ?? 0) > maxRisk || (arm.cost ?? 0) > budget) continue;
      const score = this.score(arm.id);
      if (best === null || score > bestScore) {
        best = arm;
        bestScore = score;
      }
    }
    return best;
  }

  toDict(): Record<string, unknown> {
    return {
      exploration: this.exploration,
      arms: this.arms().map((arm) => ({ ...arm, pulls: this.pulls(arm.id), mean: Number(this.mean(arm.id).toFixed(6)) })),
    };
  }
}
