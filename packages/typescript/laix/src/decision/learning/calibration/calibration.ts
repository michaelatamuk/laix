import type { Outcome } from "../../contracts.ts";
import { clamp } from "../../contracts.ts";

export interface CalibrationSample {
  confidence: number;
  correct: boolean;
  policy?: string;
}

export interface CalibrationBin {
  lower: number;
  upper: number;
  predicted: number;
  observed: number;
  count: number;
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class CalibrationReport {
  readonly samples: number;
  readonly accuracy: number;
  readonly expected: number;
  readonly error: number;
  readonly bins: CalibrationBin[];
  readonly policy: string;
  readonly smoothing: number;

  constructor(options: {
    samples: number;
    accuracy: number;
    expected: number;
    error: number;
    bins: CalibrationBin[];
    policy?: string;
    smoothing?: number;
  }) {
    this.samples = options.samples;
    this.accuracy = options.accuracy;
    this.expected = options.expected;
    this.error = options.error;
    this.bins = options.bins;
    this.policy = options.policy ?? "";
    this.smoothing = options.smoothing ?? 0;
  }

  adjust(confidence: number): number {
    for (const item of this.bins) {
      if (item.count && item.lower <= confidence && confidence < item.upper) {
        return clamp(item.observed);
      }
      if (item.count && confidence === 1 && item.upper === 1) {
        return clamp(item.observed);
      }
    }
    return clamp(confidence - (this.expected - this.accuracy));
  }

  toDict(): Record<string, unknown> {
    return {
      samples: this.samples,
      accuracy: this.accuracy,
      expected: this.expected,
      error: this.error,
      policy: this.policy,
      smoothing: this.smoothing,
      bins: this.bins.map((item) => ({ ...item })),
    };
  }
}

export function calibrationReport(
  samples: CalibrationSample[],
  options: { bins?: number; policy?: string; smoothing?: number } = {},
): CalibrationReport {
  const bins = options.bins ?? 10;
  const policy = options.policy ?? "";
  const smoothing = options.smoothing ?? 0;
  if (bins < 1) throw new Error("bins must be at least one");
  if (smoothing < 0) throw new Error("smoothing must not be negative");
  if (!samples.length) {
    return new CalibrationReport({
      samples: 0,
      accuracy: 0,
      expected: 0,
      error: 0,
      bins: [],
      policy,
      smoothing,
    });
  }

  const buckets: CalibrationSample[][] = Array.from({ length: bins }, () => []);
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
      observed: round((correct + smoothing) / (bucket.length + 2 * smoothing)),
      count: bucket.length,
    });
  }

  const accuracy = samples.filter((item) => item.correct).length / samples.length;
  const expected =
    samples.reduce((total, item) => total + item.confidence, 0) / samples.length;
  return new CalibrationReport({
    samples: samples.length,
    accuracy: round(accuracy),
    expected: round(expected),
    error: round(Math.abs(expected - accuracy)),
    bins: rows,
    policy,
    smoothing,
  });
}

export function calibrationByPolicy(
  samples: CalibrationSample[],
  options: { bins?: number; smoothing?: number } = {},
): Record<string, CalibrationReport> {
  const buckets = new Map<string, CalibrationSample[]>();
  for (const item of samples) {
    const policy = item.policy ?? "";
    const items = buckets.get(policy) ?? [];
    items.push(item);
    buckets.set(policy, items);
  }
  return Object.fromEntries(
    [...buckets.entries()]
      .sort(([left], [right]) => (left < right ? -1 : 1))
      .map(([policy, items]) => [
        policy,
        calibrationReport(items, {
          bins: options.bins,
          policy,
          smoothing: options.smoothing,
        }),
      ]),
  );
}

export function samplesFromOutcomes(
  outcomes: Outcome[],
  confidences: Record<string, number>,
  options: { policies?: Record<string, string> } = {},
): CalibrationSample[] {
  const rows: CalibrationSample[] = [];
  for (const outcome of outcomes) {
    const confidence = confidences[outcome.decisionId];
    if (confidence === undefined) continue;
    rows.push({
      confidence,
      correct: outcome.label === "helped",
      policy: options.policies?.[outcome.decisionId] ?? "",
    });
  }
  return rows;
}
