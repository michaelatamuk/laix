import {
  DecisionClient,
  type ActionOption,
  type Belief,
  type DecisionRequest,
  type Situation,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const beliefs: Belief[] = [
  {
    id: "overflow",
    proposition: "the sink is about to overflow",
    confidence: 0.95,
  },
];
const situation: Situation = {
  id: "sink-1",
  at: "2026-11-01T10:00:00Z",
  subject: "kitchen sink",
  beliefs,
  attributes: { urgency: 0.9 },
};
const options: ActionOption[] = [
  { id: "option-wait", verb: "wait", name: "keep-watching", expectedBenefit: 0.1 },
  {
    id: "option-close-valve",
    verb: "act",
    name: "close the valve",
    expectedBenefit: 0.95,
    risk: 0.05,
    reversible: true,
  },
];
const request: DecisionRequest = {
  subject: "kitchen sink",
  at: "2026-11-01T10:00:00Z",
  situation,
  options,
};
const decision = new DecisionClient().decide(request)[0]!;

console.log(
  decision.verb,
  decision.reasonCode,
  decision.actionId,
);
