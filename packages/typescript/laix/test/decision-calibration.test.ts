import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  CalibratedPolicy,
  DecisionCalibrationReport,
  calibrateDecision,
  decisionCalibrationReport,
  decisionSamplesFromOutcomes,
} from "../src/index.ts";
import type { Decision, DecisionRequest, Outcome, Policy } from "../src/index.ts";

describe("decision-level calibration", () => {
  it("bins decisions and adjusts confidence", () => {
    const samples = [
      ...Array.from({ length: 8 }, () => ({
        confidence: 0.9,
        correct: true,
        verb: "act",
        actionId: "send",
      })),
      ...Array.from({ length: 2 }, () => ({
        confidence: 0.9,
        correct: false,
        verb: "act",
        actionId: "send",
      })),
      ...Array.from({ length: 2 }, () => ({
        confidence: 0.2,
        correct: true,
        verb: "wait",
      })),
      ...Array.from({ length: 8 }, () => ({
        confidence: 0.2,
        correct: false,
        verb: "wait",
      })),
    ];
    const report = decisionCalibrationReport(samples);

    assert.equal(report.samples, 20);
    assert.equal(report.accuracy, 0.5);
    assert.equal(report.expected, 0.55);
    assert.equal(report.error, 0.05);
    assert.equal(report.adjust(0.9), 0.8);
    assert.equal(report.verbAccuracy.act, 0.8);
    assert.equal(report.actionAccuracy.send, 0.8);
  });

  it("calibrates a decision and preserves its shape", () => {
    const report = decisionCalibrationReport(
      Array.from({ length: 10 }, (_, index) => ({
        confidence: 0.9,
        correct: index < 5,
      })),
    );
    const decision: Decision = {
      verb: "act",
      confidence: 0.9,
      reasonCode: "expected_utility",
      rationale: "the valve is the best option",
      decisionId: "d1",
      actionId: "valve",
    };

    const calibrated = calibrateDecision(decision, report);

    assert.equal(calibrated.confidence, 0.5);
    assert.equal(calibrated.calibrated, true);
    assert.equal(calibrated.confidenceSource, "decision-calibration");
    assert.equal(calibrated.verb, "act");
    assert.equal(calibrated.actionId, "valve");
    assert.equal(
      (calibrated.attributes?.calibration as Record<string, unknown>).before,
      0.9,
    );
  });

  it("wraps any policy and calibrates its decisions", () => {
    class FakePolicy implements Policy {
      readonly name = "fake";

      decide(_request: DecisionRequest): Decision[] {
        return [
          {
            verb: "act",
            confidence: 0.9,
            reasonCode: "fake",
            rationale: "a fake decision",
            decisionId: "d1",
          },
        ];
      }
    }

    const report = decisionCalibrationReport(
      Array.from({ length: 10 }, (_, index) => ({
        confidence: 0.9,
        correct: index < 5,
      })),
    );
    const policy = new CalibratedPolicy(new FakePolicy(), report);
    const decisions = policy.decide({
      subject: "a",
      at: "2026-11-01T10:00:00Z",
    });

    assert.equal(policy.name, "fake.calibrated");
    assert.equal(decisions[0]!.confidence, 0.5);
    assert.equal(decisions[0]!.calibrated, true);
  });

  it("round-trips through a dict", () => {
    const report = decisionCalibrationReport(
      Array.from({ length: 10 }, (_, index) => ({
        confidence: 0.9,
        correct: index < 5,
      })),
    );
    const restored = DecisionCalibrationReport.fromDict(report.toDict());

    assert.equal(restored.samples, report.samples);
    assert.equal(restored.accuracy, report.accuracy);
    assert.equal(restored.adjust(0.9), report.adjust(0.9));
  });

  it("builds samples from decisions and outcomes", () => {
    const decision: Decision = {
      verb: "act",
      confidence: 0.8,
      reasonCode: "r",
      rationale: "why",
      decisionId: "d1",
      actionId: "a1",
    };
    const outcome = {
      id: "o1",
      decisionId: "d1",
      metric: "saved",
      before: 0,
      after: 1,
      delta: 1,
      label: "helped",
    } as Outcome;

    const samples = decisionSamplesFromOutcomes([decision], [outcome]);

    assert.equal(samples.length, 1);
    assert.equal(samples[0]!.correct, true);
    assert.equal(samples[0]!.verb, "act");
    assert.equal(samples[0]!.actionId, "a1");
  });

  it("rejects invalid options", () => {
    assert.throws(() => decisionCalibrationReport([], { bins: 0 }));
    assert.throws(() => decisionCalibrationReport([], { smoothing: -1 }));
  });
});
