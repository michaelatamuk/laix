import { execFileSync, execSync } from "node:child_process";
import { mkdtempSync, mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const tsc = join(packageRoot, "node_modules", "typescript", "bin", "tsc");

const temp = mkdtempSync(join(tmpdir(), "laix-consumer-"));
const consumer = join(temp, "consumer");
const pack = join(temp, "pack");

function quote(value) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

function run(command, args, options) {
  if (process.platform === "win32" && command.endsWith(".cmd")) {
    return execSync([command, ...args.map(quote)].join(" "), {
      stdio: "pipe",
      encoding: "utf8",
      ...options,
    });
  }
  return execFileSync(command, args, {
    stdio: "pipe",
    encoding: "utf8",
    ...options,
  });
}

try {
  mkdirSync(consumer, { recursive: true });
  mkdirSync(pack, { recursive: true });

  run(npm, ["pack", "--pack-destination", pack], { cwd: packageRoot });
  const tarball = readdirSync(pack).find((name) => name.endsWith(".tgz"));
  if (!tarball) throw new Error("npm pack did not produce a tarball");
  const spec = `file:${join(pack, tarball).replaceAll("\\", "/")}`;

  writeFileSync(
    join(consumer, "package.json"),
    JSON.stringify(
      {
        name: "laix-consumer-smoke",
        private: true,
        type: "module",
        dependencies: { laix: spec },
      },
      null,
      2,
    ),
    "utf8",
  );

  writeFileSync(
    join(consumer, "consumer.ts"),
    `import {
  DecisionClient,
  DecisionTimeline,
  ExecutionRiskPlanner,
  HumanAttentionBudget,
  LiveCompositePlanner,
} from "laix";
import type {
  ActionOption,
  Belief,
  Breakdown,
  Decision,
  DecisionRequest,
  Phase,
  RuntimeDecision,
  Situation,
} from "laix";

const situation: Situation = {
  id: "s-1",
  at: "2026-11-01T10:00:00Z",
  subject: "one decision",
  beliefs: [{ id: "b-1", proposition: "the task is real", confidence: 0.9 }],
};
const request: DecisionRequest = {
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
  situation,
};
const decision: Decision = new DecisionClient().decide(request)[0];
const budget: HumanAttentionBudget = new HumanAttentionBudget({ total: 2 });
const planner: LiveCompositePlanner = new LiveCompositePlanner();
const risk: ExecutionRiskPlanner = new ExecutionRiskPlanner();
const timeline: DecisionTimeline = new DecisionTimeline();
const option: ActionOption = { id: "a", verb: "act", name: "act" };
const belief: Belief = { id: "b", proposition: "p", confidence: 0.5 };
const breakdown: Breakdown = { total: 1 };
const phase: Phase = "observe";
const runtimeDecision: RuntimeDecision | null = null;

console.log(
  decision.verb,
  budget.remaining(),
  planner.name,
  risk.name,
  timeline.report().decisions,
  option.id,
  belief.id,
  breakdown.total,
  phase,
  runtimeDecision,
);
`,
    "utf8",
  );

  writeFileSync(
    join(consumer, "consumer.mjs"),
    `import {
  DecisionClient,
  DecisionTimeline,
  ExecutionRiskPlanner,
  HumanAttentionBudget,
  LiveCompositePlanner,
} from "laix";

const names = [
  DecisionClient,
  DecisionTimeline,
  ExecutionRiskPlanner,
  HumanAttentionBudget,
  LiveCompositePlanner,
];
if (!names.every((value) => typeof value === "function")) {
  throw new Error("the packaged runtime is missing an export");
}
console.log("consumer runtime exports: ok");
`,
    "utf8",
  );

  run(npm, ["install", "--ignore-scripts", "--no-audit", "--no-fund"], { cwd: consumer });
  run(
    process.execPath,
    [
      tsc,
      "--noEmit",
      "--strict",
      "--target",
      "ES2022",
      "--module",
      "NodeNext",
      "--moduleResolution",
      "NodeNext",
      "--lib",
      "ES2022,DOM",
      "consumer.ts",
    ],
    { cwd: consumer },
  );
  run(process.execPath, ["consumer.mjs"], { cwd: consumer });
  console.log("consumer smoke: ok");
} finally {
  rmSync(temp, { recursive: true, force: true });
}
