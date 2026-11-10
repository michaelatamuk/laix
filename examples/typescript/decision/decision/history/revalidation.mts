import {
  RevalidationPlanner,
  UtilityPlanner,
  type PlannerInput,
} from "../../../../../packages/typescript/laix/src/index.ts";

const planner = new RevalidationPlanner(new UtilityPlanner());

function decide(previous: string) {
  const problem: PlannerInput = {
    subject: "choose",
    at: "2026-11-01T10:00:00Z",
    options: [
      { id: "timid", verb: "act", name: "timid", expectedBenefit: 0.6 },
      { id: "bold", verb: "act", name: "bold", expectedBenefit: 0.9 },
    ],
    attributes: { previous_action_id: previous },
  };
  return planner.solve(problem);
}

const held = decide("bold");
const revised = decide("timid");

console.log(held.reasonCode, revised.reasonCode, revised.actionId);
