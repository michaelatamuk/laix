import { clamp } from "../../../contracts.ts";
import type { CalibrationBin } from "./calibration.ts";

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
