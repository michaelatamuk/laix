import { clamp } from "../../contracts.ts";

export interface Budget {
  maxDeepCalls?: number;
  maxCost?: number;
  maxLatencyMs?: number;
}

export interface SensingOption {
  name: string;
  tier?: "cheap" | "deep";
  cost?: number;
  latencyMs?: number;
  informationGain?: number;
}

export interface ResourcePlan {
  allowed: string[];
  skipped: Array<{ name: string; reason: string; gain: number }>;
  deepCalls: number;
  cost: number;
  reason: string;
  attributes: Record<string, unknown>;
}

export class ResourceScheduler {
  minInformationGain: number;

  constructor(options: { minInformationGain?: number } = {}) {
    this.minInformationGain = options.minInformationGain ?? 0.35;
  }

  schedule(options: SensingOption[], settings: { budget?: Budget; uncertainty?: number } = {}): ResourcePlan {
    const budget = { maxDeepCalls: 4, maxCost: 1, maxLatencyMs: 2000, ...settings.budget };
    const uncertainty = clamp(settings.uncertainty ?? 0.5);
    const allowed: string[] = [];
    const skipped: ResourcePlan["skipped"] = [];
    let deepCalls = 0;
    let cost = 0;

    for (const option of options) {
      if ((option.tier ?? "cheap") === "cheap") {
        allowed.push(option.name);
        cost += option.cost ?? 0;
        continue;
      }
      const gain = (option.informationGain ?? 0) * Math.max(uncertainty, 0.05);
      let reason: string | null = null;
      if (deepCalls >= budget.maxDeepCalls) reason = "deep-call budget exhausted";
      else if (cost + (option.cost ?? 0) > budget.maxCost) reason = "cost budget exhausted";
      else if ((option.latencyMs ?? 0) > budget.maxLatencyMs) reason = "latency budget exceeded";
      else if (gain < this.minInformationGain) reason = `information gain ${gain.toFixed(2)} below threshold ${this.minInformationGain.toFixed(2)}`;
      if (reason) {
        skipped.push({ name: option.name, reason, gain: Number(gain.toFixed(3)) });
        continue;
      }
      allowed.push(option.name);
      deepCalls += 1;
      cost += option.cost ?? 0;
    }

    return {
      allowed,
      skipped,
      deepCalls,
      cost,
      reason: "cheap continuous; deep calls admitted by gain, uncertainty and budget",
      attributes: { uncertainty: Number(uncertainty.toFixed(3)), threshold: this.minInformationGain },
    };
  }

  static shouldEscalate(confidence: number, required = 0.75): boolean {
    return clamp(confidence) < clamp(required);
  }
}
