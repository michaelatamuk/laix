import {
  HumanAttentionBudget,
  DecisionCalibrationReport,
  DecisionTimeline,
  PlannerPolicy,
  ExecutionBridge,
  LiveCompositePlanner,
  ManualClock,
  StreamSession,
  calibrateDecision,
} from "../../../../packages/typescript/laix/src/index.ts";
import type {
  ActionOption,
  Commitment,
  DecisionRequest,
  Outcome,
} from "../../../../packages/typescript/laix/src/index.ts";

const commitments: Commitment[] = [
  {
    id: "c1",
    subject: "send the report",
    due: "2026-11-01T09:00:00Z",
  },
];
const budget = new HumanAttentionBudget({ total: 1 });
const timeline = new DecisionTimeline();
const policy = new PlannerPolicy(new LiveCompositePlanner(), "live.v1");
const session = new StreamSession(policy.decide.bind(policy), {
  streamId: "DESK",
  capacity: 4,
  timeline,
  humanAttentionBudget: budget,
  clock: () => new Date("2026-11-01T10:00:00Z"),
});

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
    interruptCost: 0.2,
    params: { commitments: { fulfills: ["c1"] } },
  },
];
const request: DecisionRequest = {
  subject: "live loop",
  at: "2026-11-01T10:00:00Z",
  options,
  attributes: { commitments, human_attention_budget: budget },
};

const decision = session.observe(request)[0]!;
const action = options.find((option) => option.id === decision.actionId)!;
const bridge = new ExecutionBridge({
  handlers: { [action.name]: () => ({ done: true }) },
});
const receipt = bridge.execute(decision, { action, actor: "agent" });
const outcome: Outcome = {
  id: "o1",
  decisionId: decision.decisionId ?? "",
  metric: "resolved",
  before: 0,
  after: 1,
  delta: 1,
  label: "helped",
};
const report = new DecisionCalibrationReport({
  samples: 1,
  accuracy: 1,
  expected: decision.confidence,
  error: 1 - decision.confidence,
  bins: [],
  verbAccuracy: { [decision.verb]: 1 },
  actionAccuracy: { [decision.actionId ?? ""]: 1 },
});
const calibrated = calibrateDecision(decision, report);

console.log(
  decision.actionId,
  decision.verb,
  receipt.status,
  outcome.label,
  timeline.report().decisions,
  budget.remaining().toFixed(1),
  calibrated.confidence.toFixed(1),
);
