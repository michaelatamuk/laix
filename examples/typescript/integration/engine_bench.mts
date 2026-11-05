import { runEngineBench } from "../../../packages/typescript/laix/src/index.ts";

const report = runEngineBench();
const summary = report.summary();
console.log(report.best(), summary.mdp!.meanReward, summary["stay-baseline"]!.meanGap);
