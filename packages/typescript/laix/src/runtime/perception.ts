import { clamp } from "../contracts.ts";
import { ResourcePolicy, type Budget, type SensingOption } from "./resources.ts";

export interface Detection {
  id: string;
  detector: string;
  kind: string;
  subject: string;
  at: string;
  confidence?: number;
  severity?: string;
  payload?: Record<string, unknown>;
}

export interface PerceptionEvent {
  subject: string;
  at: string;
  payload?: Record<string, unknown>;
}

export interface PerceptionFrame {
  subject: string;
  at: string;
  detections: Detection[];
  allowed: string[];
  skipped: Array<{ name: string; reason: string; gain: number }>;
  uncertainty: number;
  deepCalls: number;
  cost: number;
  toDict(): Record<string, unknown>;
}

export interface Detector {
  name: string;
  tier?: "cheap" | "deep";
  cost?: number;
  latencyMs?: number;
  informationGain?: number;
  detect(event: PerceptionEvent): Detection[];
}

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

class Frame implements PerceptionFrame {
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

export class LiveContext {
  budget: Required<Budget>;
  policy: ResourcePolicy;
  frames: PerceptionFrame[] = [];
  private detectors = new Map<string, Detector>();

  constructor(detectors: Detector[] = [], options: { budget?: Budget; policy?: ResourcePolicy } = {}) {
    this.budget = { maxDeepCalls: 2, maxCost: 1, maxLatencyMs: 500, ...options.budget };
    this.policy = options.policy ?? new ResourcePolicy();
    for (const detector of detectors) this.register(detector);
  }

  register(detector: Detector): void {
    const name = detector.name.trim();
    if (!name) throw new Error("detector name is required");
    if (typeof detector.detect !== "function") throw new Error(`detector '${name}' has no detect method`);
    this.detectors.set(name, detector);
  }

  names(): string[] {
    return [...this.detectors.keys()];
  }

  perceive(event: PerceptionEvent, uncertainty = 0.5): PerceptionFrame {
    const options: SensingOption[] = [...this.detectors.values()].map((detector) => ({
      name: detector.name,
      tier: detector.tier ?? "cheap",
      cost: detector.cost ?? 0,
      latencyMs: detector.latencyMs ?? 0,
      informationGain: detector.informationGain ?? 0,
    }));
    const plan = this.policy.schedule(options, { budget: this.budget, uncertainty });
    const detections: Detection[] = [];
    let remaining = clamp(uncertainty);
    for (const name of plan.allowed) {
      const detector = this.detectors.get(name)!;
      const found = detector.detect(event);
      detections.push(...found);
      if (found.length > 0) {
        const best = Math.max(...found.map((item) => clamp(item.confidence ?? 0.5)));
        const gain = (detector.informationGain ?? 0) * best;
        remaining *= 1 - Math.min(0.98, gain);
      }
    }
    const frame = new Frame(event.subject, event.at, detections, plan.allowed, plan.skipped, clamp(remaining), plan.deepCalls, plan.cost);
    this.frames.push(frame);
    return frame;
  }

  feed(events: PerceptionEvent[], uncertainty = 0.5): PerceptionFrame[] {
    return events.map((event) => this.perceive(event, uncertainty));
  }

  get latest(): PerceptionFrame | null {
    return this.frames.at(-1) ?? null;
  }
}
