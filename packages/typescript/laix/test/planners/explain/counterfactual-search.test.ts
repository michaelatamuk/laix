import assert from "node:assert/strict";
import test from "node:test";

import { counterfactualSearch } from "../../../src/index.ts";

test("CDA search finds a rule threshold", () => {
  const report = counterfactualSearch(
    (values) => (values.risk! >= 0.5 ? "escalate" : "act"),
    [{ name: "risk", value: 0.4, lower: 0.2, upper: 0.8, step: 0.05 }],
    { maxChanges: 1 },
  );

  assert.equal(report.chosenId, "act");
  assert.equal(report.counterfactualId, "escalate");
  assert.equal(report.changes[0]?.name, "risk");
  assert.equal(report.changes[0]?.new, 0.5);
  assert.equal(report.distance, 0.1);
});

test("CDA search needs two changes", () => {
  const report = counterfactualSearch(
    (values) =>
      values.risk! + values.uncertainty! >= 1.2 ? "escalate" : "act",
    [
      { name: "risk", value: 0.4, lower: 0.4, upper: 0.7, step: 0.1 },
      { name: "uncertainty", value: 0.2, lower: 0.2, upper: 0.5, step: 0.1 },
    ],
    { maxChanges: 2 },
  );

  assert.equal(report.counterfactualId, "escalate");
  assert.deepEqual(
    report.changes.map((change) => change.name).sort(),
    ["risk", "uncertainty"],
  );
  assert.equal(report.distance, 0.6);
});

test("CDA search returns no counterfactual when none flips", () => {
  const report = counterfactualSearch(
    () => "act",
    [{ name: "risk", value: 0.4, lower: 0.2, upper: 0.8, step: 0.1 }],
    { maxChanges: 1 },
  );

  assert.equal(report.counterfactualId, null);
  assert.equal(report.changes.length, 0);
  assert.equal(report.distance, 0);
});
