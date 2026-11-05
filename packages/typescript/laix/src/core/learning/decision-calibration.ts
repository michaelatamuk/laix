import type { Decision } from "../contracts.ts";
import { clamp } from "../contracts.ts";
import type { Outcome } from "../contracts.ts";
import type { CalibrationBin } from "./calibration.ts";
import { DecisionCalibrationReport } from "./decision-calibration-report.ts";

export { DecisionCalibrationReport };
export { CalibratedPolicy } from "./calibrated-policy.ts";
export { calibrateDecision } from "./calibrate-decision.ts";

export interface DecisionCalibrationSample {
  confidence: number;
  correct: boolean;
  verb?: string;
  actionId?: string;
  policy?: string;
}

export interface DecisionCalibrationOptions {
  bins?: number;
  policy?: string;
  smoothing?: number;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

function rate(correct: number, total: number, smoothing: number): number {
  return total ? (correct + smoothing) / (total + 2 * smoothing) : 0;
}

function accuracyBy(
  items: DecisionCalibrationSample[],
  key: "verb" | "actionId",
): Record<string, number> {
  const buckets = new Map<string, boolean[]>();
  for (const item of items) {
    const value = item[key];
    if (!value) continue;
    const flags = buckets.get(value) ?? [];
    flags.push(item.correct);
    buckets.set(value, flags);
  }
  return Object.fromEntries(
    [...buckets.entries()]
      .sort(([left], [right]) => (left < right ? -1 : 1))
      .map(([value, flags]) => [
        value,
        round(flags.filter(Boolean).length / flags.length),
      ]),
  );
}

export function decisionCalibrationReport(
  samples: DecisionCalibrationSample[],
  options: DecisionCalibrationOptions = {},
): DecisionCalibrationReport {
  const bins = options.bins ?? 10;
  const policy = options.policy ?? "";
  const smoothing = options.smoothing ?? 0;
  if (bins < 1) throw new Error("bins must be at least one");
  if (smoothing < 0) throw new Error("smoothing must not be negative");
  if (!samples.length) {
    return new DecisionCalibrationReport({
      samples: 0,
      accuracy: 0,
      expected: 0,
      error: 0,
      bins: [],
      verbAccuracy: {},
      actionAccuracy: {},
      policy,
      smoothing,
    });
  }

  const buckets: DecisionCalibrationSample[][] = Array.from(
    { length: bins },
    () => [],
  );
  for (const item of samples) {
    const index = Math.min(Math.trunc(clamp(item.confidence) * bins), bins - 1);
    buckets[index]!.push(item);
  }

  const rows: CalibrationBin[] = [];
  for (let index = 0; index < buckets.length; index += 1) {
    const bucket = buckets[index]!;
    if (!bucket.length) continue;
    const correct = bucket.filter((item) => item.correct).length;
    rows.push({
      lower: round(index / bins),
      upper: round((index + 1) / bins),
      predicted: round(
        bucket.reduce((total, item) => total + item.confidence, 0) / bucket.length,
      ),
      observed: round(rate(correct, bucket.length, smoothing)),
      count: bucket.length,
    });
  }

  const accuracy = samples.filter((item) => item.correct).length / samples.length;
  const expected =
    samples.reduce((total, item) => total + item.confidence, 0) / samples.length;
  return new DecisionCalibrationReport({
    samples: samples.length,
    accuracy: round(accuracy),
    expected: round(expected),
    error: round(Math.abs(expected - accuracy)),
    bins: rows,
    verbAccuracy: accuracyBy(samples, "verb"),
    actionAccuracy: accuracyBy(samples, "actionId"),
    policy,
    smoothing,
  });
}

export function decisionSamplesFromOutcomes(
  decisions: Decision[],
  outcomes: Outcome[],
  options: { policies?: Record<string, string> } = {},
): DecisionCalibrationSample[] {
  const byId = new Map(
    decisions
      .filter((decision) => decision.decisionId)
      .map((decision) => [decision.decisionId!, decision]),
  );
  const rows: DecisionCalibrationSample[] = [];
  for (const outcome of outcomes) {
    const decision = byId.get(outcome.decisionId);
    if (!decision) continue;
    rows.push({
      confidence: decision.confidence,
      correct: outcome.label === "helped",
      verb: decision.verb,
      actionId: decision.actionId ?? "",
      policy: options.policies?.[decision.decisionId!] ?? "",
    });
  }
  return rows;
}
