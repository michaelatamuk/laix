import {
  CaseBasedPlanner,
  ConflictResolutionPlanner,
  type PlannerInput,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const casePlan = new CaseBasedPlanner([
  { subject: "send the report", actionId: "send-now" },
]).solve({
  subject: "send the report today",
  at: "2026-11-01T10:00:00Z",
  options: [
    { id: "send-now", verb: "act", name: "send now" },
    { id: "send-later", verb: "wait", name: "send later" },
  ],
});
const conflictProblem: PlannerInput = {
  subject: "choose",
  at: "2026-11-01T10:00:00Z",
  options: [{ id: "a", verb: "act", name: "a" }],
  attributes: {
    goal_conflicts: [
      { id: "g1", left: "speed", right: "safety", severity: 0.9 },
    ],
  },
};
const conflictPlan = new ConflictResolutionPlanner().solve(conflictProblem);

console.log("case", casePlan.actionId, casePlan.reasonCode);
console.log("conflict", conflictPlan.verb, conflictPlan.reasonCode);
