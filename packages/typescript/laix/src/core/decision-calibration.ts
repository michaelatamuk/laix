import type { Decision, DecisionRequest } from "./contracts.ts";
import { clamp } from "./contracts.ts";
import type { Outcome } from "./contracts.ts";
import type { CalibrationBin } from "./calibration.ts";
import type { Policy } from "./policies/registry.ts";

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

export class DecisionCalibrationReport {
  readonly samples: number;
  readonly accuracy: number;
  readonly expected: number;
  readonly error: number;
  readonly bins: CalibrationBin[];
  readonly verbAccuracy: Record<string, number>;
  readonly actionAccuracy: Record<string, number>;
  readonly policy: string;
  readonly smoothing: number;

  constructor(options: {
    samples: number;
    accuracy: number;
    expected: number;
    error: number;
    bins: CalibrationBin[];
    verbAccuracy: Record<string, number>;
    actionAccuracy: Record<string, number>;
    policy?: string;
    smoothing?: number;
  }) {
    this.samples = options.samples;
    this.accuracy = options.accuracy;
    this.expected = options.expected;
    this.error = options.error;
    this.bins = options.bins;
    this.verbAccuracy = options.verbAccuracy;
    this.actionAccuracy = options.actionAccuracy;
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
      verb_accuracy: { ...this.verbAccuracy },
      action_accuracy: { ...this.actionAccuracy },
    };
  }

  static fromDict(payload: Record<string, unknown>): DecisionCalibrationReport {
    const bins = Array.isArray(payload.bins)
      ? (payload.bins as CalibrationBin[])
      : [];
    return new DecisionCalibrationReport({
      samples: Number(payload.samples ?? 0),
      accuracy: Number(payload.accuracy ?? 0),
      expected: Number(payload.expected ?? 0),
      error: Number(payload.error ?? 0),
      bins,
      verbAccuracy: (payload.verb_accuracy as Record<string, number>) ?? {},
      actionAccuracy: (payload.action_accuracy as Record<string, number>) ?? {},
      policy: String(payload.policy ?? ""),
      smoothing: Number(payload.smoothing ?? 0),
    });
  }
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

export class CalibratedPolicy implements Policy {
  readonly name: string;
  readonly policy: Policy;
  readonly report: DecisionCalibrationReport;

  constructor(
    policy: Policy,
    report: DecisionCalibrationReport,
    name?: string,
  ) {
    this.policy = policy;
    this.report = report;
    this.name = name ?? `${policy.name}.calibrated`;
  }

  decide(request: DecisionRequest): Decision[] {
    return this.policy
      .decide(request)
      .map((decision) => calibrateDecision(decision, this.report));
  }
}

export function calibrateDecision(
  decision: Decision,
  report: DecisionCalibrationReport,
  options: { source?: string } = {},
): Decision {
  if (report.samples === 0) return decision;
  const adjusted = report.adjust(decision.confidence);
  return {
    ...decision,
    confidence: adjusted,
    calibrated: true,
    confidenceSource: options.source ?? "decision-calibration",
    attributes: {
      ...(decision.attributes ?? {}),
      calibration: {
        before: decision.confidence,
        after: adjusted,
        samples: report.samples,
        accuracy: report.accuracy,
      },
    },
  };
}
