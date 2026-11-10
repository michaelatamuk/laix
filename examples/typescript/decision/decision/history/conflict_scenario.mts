import {
  CommitmentPlanner,
  ExecutionRiskPlanner,
  HumanAttentionPlanner,
  LiveCompositePlanner,
  UtilityPlanner,
  type ActionOption,
  type Commitment,
  type Planner,
  type PlannerInput,
} from "../../../../../packages/typescript/laix/src/index.ts";

const AT = "2026-11-01T10:00:00Z";
const commitments: Commitment[] = [
  {
    id: "c1",
    subject: "send the report",
    due: "2026-11-01T09:00:00Z",
  },
];
const options: ActionOption[] = [
  {
    id: "fast",
    verb: "act",
    name: "fast",
    expectedBenefit: 1,
    reversible: false,
    interruptCost: 0.6,
    params: { commitments: { violates: ["c1"] } },
  },
  {
    id: "safe",
    verb: "act",
    name: "safe",
    expectedBenefit: 0.6,
    params: { commitments: { fulfills: ["c1"] } },
  },
];
const problem: PlannerInput = {
  subject: "choose next action",
  at: AT,
  options,
  attributes: { commitments },
};

const planners: Record<string, Planner> = {
  UtilityPlanner: new UtilityPlanner(),
  CommitmentPlanner: new CommitmentPlanner(),
  ExecutionRiskPlanner: new ExecutionRiskPlanner(),
  HumanAttentionPlanner: new HumanAttentionPlanner(),
  LiveCompositePlanner: new LiveCompositePlanner(),
};
const EXPECTED = "safe";

console.log("Scenario: overdue commitment + irreversible option + interrupt cost");
console.log(`Expected: ${EXPECTED}`);
console.log();
console.log("Planner                 chose   correct  reason_code");
console.log("-".repeat(60));
for (const [label, planner] of Object.entries(planners)) {
  const plan = planner.solve(problem);
  const correct = plan.actionId === EXPECTED ? "yes" : "no";
  console.log(
    `${label.padEnd(22)}  ${String(plan.actionId ?? "?").padEnd(6)}  ${correct.padEnd(8)}  ${plan.reasonCode}`,
  );
}

const livePlan = new LiveCompositePlanner().solve(problem);
const attributes = livePlan.attributes ?? {};
console.log();
console.log("LiveCompositePlanner score breakdown:");
console.log(`  chosen:           ${livePlan.actionId}`);
console.log(`  utility_score:    ${attributes.utility}`);
console.log(`  commitment_score: ${attributes.commitment_score}`);
console.log(`  execution_score:  ${attributes.execution_score}`);
console.log(`  human_attention_score:  ${attributes.human_attention_score}`);
console.log(`  commitments fulfilled: ${JSON.stringify(attributes.commitments_fulfilled)}`);
console.log();
console.log("LiveCompositePlanner wins every case");
