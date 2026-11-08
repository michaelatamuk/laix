import { clamp } from "../core/contracts.ts";
import type { Detection, Detector, PerceptionEvent, PerceptionFrame } from "../core/domain/perception/perception.ts";
import { ResourceScheduler, type Budget, type SensingOption } from "../core/engines/sensing/resources.ts";
import { CallableDetector } from "./callable-detector.ts";
import { Frame } from "./frame.ts";

export { CallableDetector };

export class LiveContext {
  budget: Required<Budget>;
  policy: ResourceScheduler;
  frames: PerceptionFrame[] = [];
  private detectors = new Map<string, Detector>();

  constructor(detectors: Detector[] = [], options: { budget?: Budget; policy?: ResourceScheduler } = {}) {
    this.budget = { maxDeepCalls: 2, maxCost: 1, maxLatencyMs: 500, ...options.budget };
    this.policy = options.policy ?? new ResourceScheduler();
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
