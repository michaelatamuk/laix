import {
  calibrationReport,
} from "../../../packages/typescript/laix/src/index.ts";
import type {
  CalibrationSample,
} from "../../../packages/typescript/laix/src/index.ts";

const samples: CalibrationSample[] = Array.from({ length: 10 }, (_, index) => ({
  confidence: 0.9,
  correct: index < 5,
}));
const report = calibrationReport(samples);
console.log(report.expected, report.accuracy, report.error, report.adjust(0.9));
