import {
  runLiveBench,
} from "../../../../../packages/typescript/laix/src/index.ts";

const report = runLiveBench();
for (const name of ["utility", "commitment", "execution", "attention", "live"]) {
  const metric = report.metrics.find((item) => item.planner === name)!;
  console.log(name, metric.accuracy.toFixed(2), metric.safetyViolations);
}
