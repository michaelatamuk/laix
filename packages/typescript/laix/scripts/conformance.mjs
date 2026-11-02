/**
 * Canonical attention-contract conformance.
 *
 * Reads `packages/contracts/attention.v1.json` (the same file the Python implementation
 * uses) and fails if any of the 23 behavioural cases disagree.
 *
 * Run from packages/typescript/laix:
 *   node --experimental-strip-types scripts/conformance.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { decideAttention } from "../src/index.ts";

const source = new URL("../../../contracts/attention.v1.json", import.meta.url);
const fixture = JSON.parse(readFileSync(source, "utf8"));

const rows = [];
let pass = 0;

for (const testCase of fixture.cases) {
  const decisions = decideAttention(testCase.context, testCase.signals);
  const byId = new Map(decisions.map((decision) => [decision.signalId, decision]));

  for (const expected of testCase.expected) {
    const actual = byId.get(expected.signalId);
    const problems = [];
    if (!actual) {
      problems.push("missing decision");
    } else {
      if (actual.verb !== expected.verb) problems.push(`verb ${actual.verb} != ${expected.verb}`);
      if (expected.reason_code !== undefined && actual.reasonCode !== expected.reason_code) {
        problems.push(`reason ${actual.reasonCode} != ${expected.reason_code}`);
      }
      if (expected.deliver !== undefined && actual.deliver !== expected.deliver) {
        problems.push(`deliver ${actual.deliver} != ${expected.deliver}`);
      }
      if (expected.record !== undefined && actual.record !== expected.record) {
        problems.push(`record ${actual.record} != ${expected.record}`);
      }
      if (expected.requires_approval !== undefined && actual.requiresApproval !== expected.requires_approval) {
        problems.push(`requires_approval ${actual.requiresApproval} != ${expected.requires_approval}`);
      }
      if (typeof expected.score === "number" && Math.abs(actual.score - expected.score) > 0.01) {
        problems.push(`score ${actual.score} != ${expected.score}`);
      }
      if (typeof expected.cost_of_waiting === "number" && Math.abs(actual.costOfWaiting - expected.cost_of_waiting) > 0.01) {
        problems.push(`cost_of_waiting ${actual.costOfWaiting} != ${expected.cost_of_waiting}`);
      }
      if ("undo_hint" in expected && (expected.undo_hint ?? null) !== actual.undoHint) {
        problems.push(`undo_hint ${actual.undoHint} != ${expected.undo_hint}`);
      }
      if (expected.reversible !== undefined && actual.reversible !== expected.reversible) {
        problems.push(`reversible ${actual.reversible} != ${expected.reversible}`);
      }
    }
    if (problems.length === 0) pass += 1;
    rows.push({
      case: testCase.id,
      signal: expected.signalId,
      expected: expected.action,
      actual: actual?.action ?? "missing",
      pass: problems.length === 0,
      problems,
    });
  }
}

const total = rows.length;
const lines = [
  "# Canonical attention conformance",
  "",
  `- Contract: \`${fixture.contract}\` v${fixture.version}`,
  `- Cases: **${total}**`,
  `- Decisions compared: **${pass} / ${total}**`,
  "",
  "| case | signal | expected | actual | pass | problems |",
  "|---|---|---|---|---|---|",
  ...rows.map(
    (row) =>
      `| ${row.case} | ${row.signal} | ${row.expected} | ${row.actual} | ${row.pass ? "pass" : "fail"} | ${row.problems.join("; ") || "-"} |`,
  ),
  "",
];

writeFileSync(new URL("../CONFORMANCE.md", import.meta.url), lines.join("\n"), "utf8");
console.log(`attention conformance: ${pass}/${total} decisions agree`);
if (pass !== total) {
  for (const row of rows.filter((item) => !item.pass)) {
    console.error(`${row.case}/${row.signal}: ${row.problems.join("; ")}`);
  }
  process.exitCode = 1;
}
