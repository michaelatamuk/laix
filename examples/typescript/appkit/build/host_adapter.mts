import {
  DecisionClient,
  type ActionOption,
  type DecisionRequest,
  type Situation,
} from "../../../../packages/typescript/laix/src/index.ts";

const options: ActionOption[] = [
  { id: "wait", verb: "wait", name: "wait", expectedBenefit: 0.1 },
  { id: "look", verb: "observe", name: "look closer", expectedBenefit: 0.5 },
  { id: "ask", verb: "ask", name: "call the owner", expectedBenefit: 0.4 },
  {
    id: "valve",
    verb: "act",
    name: "turn off the valve",
    expectedBenefit: 0.95,
    risk: 0.05,
    reversible: true,
  },
  { id: "manager", verb: "escalate", name: "call the manager", expectedBenefit: 0.7 },
];
const situation: Situation = {
  id: "leak-1",
  at: "2026-11-01T10:00:00Z",
  subject: "bathroom leak",
  beliefs: [
    { id: "leak", proposition: "water is leaking", confidence: 0.9 },
  ],
  constraints: [{ id: "risk-limit", kind: "risk", value: 0.2, hard: true }],
  attributes: { urgency: 0.9 },
};
const request: DecisionRequest = {
  subject: "bathroom leak",
  at: "2026-11-01T10:00:00Z",
  situation,
  options,
  confidence: 0.88,
  confidenceSource: "host-calibrated",
  calibrated: true,
};
const decision = new DecisionClient().decide(request)[0]!;
const basisKind = decision.intent ? "intent" : "reason";

console.log(
  decision.verb,
  decision.actionId,
  decision.confidenceSource,
  decision.calibrated,
  basisKind,
);
