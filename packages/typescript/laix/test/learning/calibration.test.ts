import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  calibrationByPolicy,
  calibrationReport,
  samplesFromOutcomes,
} from "../../src/index.ts";
import type { CalibrationSample, Outcome } from "../../src/index.ts";

function samples(policy = ""): CalibrationSample[] {
  return Array.from({ length: 10 }, (_, index) => ({
    confidence: 0.9,
    correct: index < 5,
    policy,
  }));
}

describe("calibration", () => {
  it("compares expected and observed", () => {
    const report = calibrationReport(samples());

    assert.equal(report.samples, 10);
    assert.equal(report.expected, 0.9);
    assert.equal(report.accuracy, 0.5);
    assert.equal(report.error, 0.4);
    assert.equal(report.bins[0]!.count, 10);
    assert.equal(report.bins[0]!.observed, 0.5);
    assert.equal(report.adjust(0.9), 0.5);
  });

  it("groups reports by policy", () => {
    const reports = calibrationByPolicy([...samples("rules"), ...samples("bandit")]);

    assert.deepEqual(Object.keys(reports).sort(), ["bandit", "rules"]);
    assert.equal(reports.rules!.samples, 10);
  });

  it("supports Laplace smoothing", () => {
    const report = calibrationReport(
      [{ confidence: 0.9, correct: true }],
      { smoothing: 1 },
    );

    assert.equal(report.smoothing, 1);
    assert.equal(report.bins[0]!.observed, 0.666667);
    assert.equal(report.adjust(0.9), 0.666667);
  });

  it("turns outcomes into samples", () => {
    const outcomes: Outcome[] = [
      {
        id: "o1",
        decisionId: "d1",
        metric: "precision",
        before: 0.5,
        after: 0.8,
        delta: 0.3,
        label: "helped",
      },
      {
        id: "o2",
        decisionId: "d2",
        metric: "precision",
        before: 0.5,
        after: 0.4,
        delta: -0.1,
        label: "hurt",
      },
    ];
    const rows = samplesFromOutcomes(
      outcomes,
      { d1: 0.8, d2: 0.7 },
      { policies: { d1: "rules", d2: "rules" } },
    );

    assert.deepEqual(rows.map((item) => item.correct), [true, false]);
    assert.deepEqual([...new Set(rows.map((item) => item.policy))], ["rules"]);
  });
});
