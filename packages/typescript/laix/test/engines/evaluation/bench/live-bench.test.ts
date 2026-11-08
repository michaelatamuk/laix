import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  UtilityPlanner,
  defaultCases,
  defaultPlanners,
  liveBenchSummary,
  runLiveBench,
} from "../../../../src/index.ts";

function row(
  report: ReturnType<typeof runLiveBench>,
  caseName: string,
  planner: string,
) {
  return report.rows.find(
    (item) => item.case === caseName && item.planner === planner,
  )!;
}

describe("training-free live benchmark", () => {
  it("covers every case and planner", () => {
    const report = runLiveBench();

    assert.equal(report.cases.length, defaultCases().length);
    assert.equal(report.planners.length, Object.keys(defaultPlanners()).length);
    assert.equal(
      report.rows.length,
      report.cases.length * report.planners.length,
    );
    assert.ok(report.metrics.every((item) => item.accuracy >= 0 && item.accuracy <= 1));
  });

  it("shows the differentiated planners", () => {
    const report = runLiveBench();

    assert.equal(row(report, "commitment", "commitment").correct, true);
    assert.equal(row(report, "commitment", "utility").correct, false);
    assert.equal(row(report, "attention", "attention").correct, true);
    assert.equal(row(report, "attention", "utility").correct, false);
    assert.equal(row(report, "irreversible", "execution").correct, true);
  });

  it("lets the highest-benefit baseline break a hard limit", () => {
    const report = runLiveBench();
    const metrics = Object.fromEntries(
      report.metrics.map((item) => [item.planner, item]),
    );

    assert.ok(metrics.benefit!.safetyViolations >= 1);
    assert.match(liveBenchSummary(report), /accuracy/);
  });

  it("runs a custom case and planner", () => {
    const first = defaultCases()[0]!;
    const report = runLiveBench([first], { utility: new UtilityPlanner() });

    assert.deepEqual(report.cases, [first.name]);
    assert.deepEqual(report.planners, ["utility"]);
    assert.equal(report.rows.length, 1);
    assert.equal(report.metrics[0]!.decisions, 1);
  });
});
