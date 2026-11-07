/** LAIX-Bench for the TypeScript package. */
import { runBench, suiteNames } from "../src/appkit/bench.ts";
import { runPlannerBench } from "../src/appkit/planner-bench.ts";

const args = process.argv.slice(2);
const suites = [];
let json = false;
let list = false;
let planners = false;
let failUnder = 1;

for (let index = 0; index < args.length; index += 1) {
  const arg = args[index];
  if (arg === "--json") json = true;
  else if (arg === "--list") list = true;
  else if (arg === "--planners") planners = true;
  else if (arg === "--suite") suites.push(args[++index]);
  else if (arg === "--fail-under") failUnder = Number(args[++index]);
  else {
    console.error(`unknown argument: ${arg}`);
    process.exit(2);
  }
}

if (planners) {
  const report = runPlannerBench();
  if (json) {
    console.log(JSON.stringify(report.toDict(), null, 2));
  } else {
    console.log("planner                  scenario               reward  steps      gap");
    console.log("-".repeat(70));
    for (const row of report.rows) {
      const gap = row.optimalityGap === null ? "n/a" : row.optimalityGap.toFixed(3);
      console.log(
        `${row.planner.padEnd(24)} ${row.scenario.padEnd(20)} ${row.totalReward.toFixed(3).padStart(8)} ${String(row.steps).padStart(6)} ${gap.padStart(8)}`,
      );
    }
    console.log("-".repeat(70));
    console.log(`${"best".padEnd(24)} ${report.best() ?? "none"}`);
  }
  process.exit(0);
}

if (list) {
  const report = runBench();
  for (const name of suiteNames()) {
    const row = report.bySuite()[name];
    console.log(`${name.padEnd(24)} ${row.cases} cases`);
  }
  process.exit(0);
}

const unknown = suites.filter((name) => !suiteNames().includes(name));
if (unknown.length) {
  console.error(`unknown suite: ${unknown.join(", ")}`);
  process.exit(2);
}

const report = runBench(suites.length ? suites : undefined);
if (json) {
  console.log(JSON.stringify(report.toDict(), null, 2));
} else {
  console.log("suite                     cases  passed  agreement");
  console.log("-".repeat(51));
  for (const [name, row] of Object.entries(report.bySuite())) {
    console.log(`${name.padEnd(24)} ${String(row.cases).padStart(6)} ${String(row.passed).padStart(7)} ${row.agreement.toFixed(3).padStart(10)}`);
  }
  console.log("-".repeat(51));
  console.log(`${"overall".padEnd(24)} ${String(report.total).padStart(6)} ${String(report.passed).padStart(7)} ${report.agreement.toFixed(3).padStart(10)}`);
  for (const row of report.rows.filter((item) => !item.passed)) {
    console.log(`FAIL ${row.suite}/${row.case}: ${row.mismatches.join("; ")}`);
  }
}

process.exit(report.agreement >= failUnder ? 0 : 1);
