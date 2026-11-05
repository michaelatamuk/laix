import type { ActionOption } from "../../contracts.ts";

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
