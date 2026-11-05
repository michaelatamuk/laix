import {
  calibrateDecision,
  decisionCalibrationReport,
} from "../../../packages/typescript/laix/src/index.ts";
import type { Decision } from "../../../packages/typescript/laix/src/index.ts";

const samples = Array.from({ length: 10 }, (_, index) => ({
  confidence: 0.9,
  correct: index < 5,
}));
const report = decisionCalibrationReport(samples);
const decision: Decision = {
  verb: "act",
  confidence: 0.9,
  reasonCode: "expected_utility",
  rationale: "the valve is the best option",
  decisionId: "d1",
  actionId: "valve",
};
const calibrated = calibrateDecision(decision, report);

console.log(decision.confidence, calibrated.confidence, calibrated.confidenceSource);
