import type { Detection, PerceptionFrame } from "../core/perception.ts";

export class Frame implements PerceptionFrame {
  subject: string;
  at: string;
  detections: Detection[];
  allowed: string[];
  skipped: Array<{ name: string; reason: string; gain: number }>;
  uncertainty: number;
  deepCalls: number;
  cost: number;

  constructor(
    subject: string,
    at: string,
    detections: Detection[],
    allowed: string[],
    skipped: Array<{ name: string; reason: string; gain: number }>,
    uncertainty: number,
    deepCalls: number,
    cost: number,
  ) {
    this.subject = subject;
    this.at = at;
    this.detections = detections;
    this.allowed = allowed;
    this.skipped = skipped;
    this.uncertainty = uncertainty;
    this.deepCalls = deepCalls;
    this.cost = cost;
  }

  toDict(): Record<string, unknown> {
    return {
      subject: this.subject,
      at: this.at,
      detections: this.detections,
      allowed: this.allowed,
      skipped: this.skipped,
      uncertainty: Number(this.uncertainty.toFixed(6)),
      deepCalls: this.deepCalls,
      cost: Number(this.cost.toFixed(6)),
    };
  }
}
