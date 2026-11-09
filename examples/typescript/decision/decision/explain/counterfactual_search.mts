import { counterfactualSearch } from "../../../../../packages/typescript/laix/src/index.ts";

const report = counterfactualSearch(
  (values) => (values.risk! >= 0.5 ? "escalate" : "act"),
  [{ name: "risk", value: 0.4, lower: 0.2, upper: 0.8, step: 0.05 }],
  { maxChanges: 1 },
);

console.log(
  report.chosenId,
  report.counterfactualId,
  report.changes[0]?.new,
  report.distance,
);
