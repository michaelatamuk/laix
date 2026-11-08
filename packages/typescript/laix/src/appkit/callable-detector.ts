import type { Detection, Detector, PerceptionEvent } from "../core/domain/perception/perception.ts";

export class CallableDetector implements Detector {
  name: string;
  tier: "cheap" | "deep";
  cost: number;
  latencyMs: number;
  informationGain: number;
  private handler: (event: PerceptionEvent) => Detection[];

  constructor(name: string, handler: (event: PerceptionEvent) => Detection[], options: { tier?: "cheap" | "deep"; cost?: number; latencyMs?: number; informationGain?: number } = {}) {
    this.name = name;
    this.handler = handler;
    this.tier = options.tier ?? "cheap";
    this.cost = options.cost ?? 0;
    this.latencyMs = options.latencyMs ?? 0;
    this.informationGain = options.informationGain ?? 0;
  }

  detect(event: PerceptionEvent): Detection[] {
    return this.handler(event);
  }
}
