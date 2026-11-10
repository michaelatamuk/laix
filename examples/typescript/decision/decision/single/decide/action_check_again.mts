import {
  DecisionClient,
  type ActionOption,
  type DecisionRequest,
  type Situation,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const situation: Situation = {
  id: "parcel-1",
  at: "2026-11-01T10:00:00Z",
  subject: "late parcel",
  beliefs: [
    { id: "late", proposition: "the parcel is late", confidence: 0.6 },
  ],
  attributes: { urgency: 0.8, needs_more_info: true },
};
const options: ActionOption[] = [
  { id: "option-wait", verb: "wait", name: "keep waiting", expectedBenefit: 0.2 },
  {
    id: "option-check-tracking",
    verb: "observe",
    name: "read the tracking page",
    expectedBenefit: 0.6,
  },
  {
    id: "option-ask-courier",
    verb: "ask",
    name: "ask the courier",
    expectedBenefit: 0.4,
  },
];
const request: DecisionRequest = {
  subject: "late parcel",
  at: "2026-11-01T10:00:00Z",
  situation,
  options,
};
const decision = new DecisionClient().decide(request)[0]!;

console.log(decision.verb, decision.reasonCode, decision.actionId);
