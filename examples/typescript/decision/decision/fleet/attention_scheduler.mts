import { AttentionScheduler } from "../../../../../packages/typescript/laix/src/index.ts";

const schedule = new AttentionScheduler().schedule(
  [
    {
      id: "refund-approval",
      risk: 0.9,
      commitment: true,
      informationValue: 0.4,
      reviewCost: 1,
      deadline: "2026-11-01T10:05:00Z",
    },
    {
      id: "routine-review",
      risk: 0.2,
      reviewCost: 1,
      deadline: "2026-11-01T12:00:00Z",
    },
    {
      id: "check-evidence",
      risk: 0.4,
      informationValue: 0.6,
      reviewCost: 0.5,
    },
  ],
  { now: "2026-11-01T10:00:00Z", budget: 1.5 },
);

console.log(schedule.selected.map((row) => row.candidateId).join(","));
console.log(schedule.deferred.map((row) => row.candidateId).join(","));
console.log(schedule.spent, schedule.budget);
