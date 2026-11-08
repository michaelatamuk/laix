/** Live Context: cheap detectors always run, deep ones only when they pay off. */
import {
  CallableDetector,
  LiveContext,
} from "../../../../packages/typescript/laix/src/index.ts";

const found = (name: string, confidence: number) => (event: { subject: string; at: string }) => [{
  id: `${name}-${event.at}`,
  detector: name,
  kind: "presence",
  subject: event.subject,
  at: event.at,
  confidence,
}];

const context = new LiveContext([
  new CallableDetector("motion", found("motion", 0.8), { informationGain: 0.2 }),
  new CallableDetector("read-label", found("read-label", 0.95), { tier: "deep", cost: 0.1, latencyMs: 200, informationGain: 0.9 }),
  new CallableDetector("transcribe", found("transcribe", 0.9), { tier: "deep", cost: 0.1, latencyMs: 900, informationGain: 0.9 }),
]);

const frame = context.perceive({ subject: "kitchen", at: "2026-11-01T10:00:00Z" }, 0.8);
console.log(frame.allowed, frame.skipped.map((item) => item.name), frame.detections.length, frame.uncertainty.toFixed(3));
