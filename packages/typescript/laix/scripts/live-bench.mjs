/** Run the shared live-bench cases in TypeScript and compare with Python. */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { defaultPlanners } from "../src/core/bench/live-bench.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "../../../..");
const RESULTS = resolve(ROOT, "results/live_bench_v2");
const CASES = resolve(ROOT, "benchmarks/live");

const args = process.argv.slice(2);
let split = "test";
let compare = true;
for (let index = 0; index < args.length; index += 1) {
  const arg = args[index];
  if (arg === "--split") split = args[++index];
  else if (arg === "--no-compare") compare = false;
  else {
    console.error(`unknown argument: ${arg}`);
    process.exit(2);
  }
}

function actionOption(raw) {
  const params = {};
  if (raw.commitments) params.commitments = raw.commitments;
  if (raw.unknown_risk !== undefined && raw.unknown_risk !== null) {
    params.unknown_risk = raw.unknown_risk;
  }
  return {
    id: raw.id,
    verb: raw.verb,
    name: raw.name,
    expectedBenefit: raw.expected_benefit ?? 0,
    cost: raw.cost ?? 0,
    risk: raw.risk ?? 0,
    interruptCost: raw.interrupt_cost ?? 0,
    latencyMs: raw.latency_ms ?? 0,
    reversible: raw.reversible ?? true,
    requiresApproval: raw.requires_approval ?? false,
    params,
  };
}

function problem(raw) {
  const attributes = {};
  if (raw.commitments && raw.commitments.length) attributes.commitments = raw.commitments;
  if (raw.attention_budget) attributes.attention_budget = raw.attention_budget;
  if (raw.approvals) attributes.approvals = raw.approvals;
  return {
    subject: raw.subject,
    at: raw.at,
    situation: raw.situation ?? undefined,
    options: (raw.options ?? []).map(actionOption),
    attributes,
  };
}

function loadCases() {
  const path = resolve(CASES, `${split}-cases-v1.json`);
  if (!existsSync(path)) {
    console.error(`missing case file: ${path}`);
    console.error("Run: python scripts/generate_live_cases.py");
    process.exit(2);
  }
  const payload = JSON.parse(readFileSync(path, "utf8"));
  return payload.cases.map((item) => ({
    id: item.id,
    expected: item.expected_actions ?? [],
    tags: item.tags ?? [],
    problem: problem(item.problem),
  }));
}

function loadPythonRows() {
  const path = resolve(RESULTS, "raw.jsonl");
  if (!existsSync(path)) return null;
  const rows = new Map();
  for (const line of readFileSync(path, "utf8").split(/\r?\n/)) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    rows.set(`${row.case}\u0000${row.planner}`, row.action_id ?? null);
  }
  return rows;
}

const cases = loadCases();
const planners = defaultPlanners();
const rows = [];
for (const [plannerName, engine] of Object.entries(planners)) {
  for (const testCase of cases) {
    const started = performance.now();
    const plan = engine.solve(testCase.problem);
    rows.push({
      case: testCase.id,
      planner: plannerName,
      actionId: plan.actionId ?? null,
      verb: plan.verb,
      expected: testCase.expected,
      correct: testCase.expected.length ? testCase.expected.includes(plan.actionId ?? "") : null,
      latencyMs: performance.now() - started,
    });
  }
}

const summary = { schema: "laix/typescript-live-bench/v1", split, cases: cases.length, planners: {} };
for (const plannerName of Object.keys(planners)) {
  const selected = rows.filter((row) => row.planner === plannerName);
  const checked = selected.filter((row) => row.correct !== null);
  summary.planners[plannerName] = {
    cases: selected.length,
    checked: checked.length,
    correct: checked.filter((row) => row.correct).length,
    accuracy: checked.length
      ? checked.filter((row) => row.correct).length / checked.length
      : 0,
  };
}

let parity = null;
if (compare) {
  const python = loadPythonRows();
  if (python === null) {
    console.error("missing Python raw results: results/live_bench_v2/raw.jsonl");
    process.exit(2);
  }
  const mismatches = [];
  let compared = 0;
  for (const row of rows) {
    const key = `${row.case}\u0000${row.planner}`;
    if (!python.has(key)) continue;
    compared += 1;
    if (python.get(key) !== row.actionId) {
      mismatches.push({ case: row.case, planner: row.planner, python: python.get(key), typescript: row.actionId });
    }
  }
  parity = { compared, mismatches: mismatches.length, details: mismatches.slice(0, 20) };
  summary.parity = parity;
}

mkdirSync(RESULTS, { recursive: true });
writeFileSync(
  resolve(RESULTS, "typescript-summary.json"),
  `${JSON.stringify(summary, null, 2)}\n`,
  "utf8",
);

console.log(`TypeScript live bench — ${split} split, ${cases.length} cases`);
console.log("planner       accuracy   correct / checked");
console.log("-------------------------------------------");
for (const name of Object.keys(summary.planners).sort()) {
  const item = summary.planners[name];
  console.log(
    `${name.padEnd(12)} ${(item.accuracy * 100).toFixed(2).padStart(8)}%   ${String(item.correct).padStart(3)} / ${item.checked}`,
  );
}

if (parity) {
  console.log(
    `\nPython/TypeScript action parity: ${parity.compared - parity.mismatches}/${parity.compared} agree`,
  );
  if (parity.mismatches) {
    console.error("mismatches:");
    for (const item of parity.details) {
      console.error(
        `  - ${item.case}/${item.planner}: python=${item.python} typescript=${item.typescript}`,
      );
    }
    process.exit(1);
  }
}
