/** Run LAIX-Bench from TypeScript. */
import { runBench } from "../../../../packages/typescript/laix/src/index.ts";

const report = runBench();
console.log(report.total, report.passed, report.agreement);
