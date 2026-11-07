import { runPlannerBench } from "../../../packages/typescript/laix/src/index.ts";

const report = runPlannerBench();
const summary = report.summary();
console.log(report.best(), summary.mdp!.meanReward, summary["stay-baseline"]!.meanGap);
