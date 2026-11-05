import type { Decision } from "../contracts.ts";
import type { DecisionCalibrationReport } from "./decision-calibration-report.ts";

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
