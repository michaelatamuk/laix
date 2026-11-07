import assert from "node:assert/strict";
import test from "node:test";

import { counterfactualAttribution } from "../../src/index.ts";
import type { Decision } from "../../src/index.ts";

function decision(): Decision {
  return {
    verb: "ask",
    confidence: 0.8,
    reasonCode: "value_of_decision",
    rationale: "ask balances the terms",
    actionId: "ask",
    score: 1,
    attributes: {
      utility: 0.5,
      commitment_score: 0.6,
      execution_score: 0,
      human_attention_score: -0.1,
    },
    alternatives: [
      {
        action_id: "pay",
        verb: "act",
        utility: 0.8,
        commitment: -0.2,
        execution: -0.3,
        human_attention: -0.1,
        total: 0.2,
      },
      {
        action_id: "wait",
        verb: "wait",
        utility: 0.2,
        commitment: 0,
        execution: 0,
        human_attention: 0,
        total: 0.2,
      },
    ],
  };
}

test("CDA finds the smallest counterfactual gap", () => {
  const report = counterfactualAttribution(decision());

  assert.equal(report.chosenId, "ask");
  assert.ok(report.minimal);
  assert.equal(report.minimal?.alternativeId, "pay");
  assert.ok((report.minimal?.delta ?? 0) >= 0.8);
  assert.ok((report.minimal?.delta ?? 1) <= 0.80001);
  assert.ok(
    (report.counterfactuals[0]?.delta ?? 0) <=
      (report.counterfactuals.at(-1)?.delta ?? 0),
  );
});

test("CDA handles a decision without component scores", () => {
  const report = counterfactualAttribution({
    verb: "ask",
    confidence: 0.8,
    reasonCode: "x",
    rationale: "x",
    actionId: "ask",
    score: 1,
    attributes: {},
    alternatives: [{ action_id: "pay", total: 0.2 }],
  });

  assert.equal(report.counterfactuals.length, 0);
  assert.equal(report.minimal, null);
});
