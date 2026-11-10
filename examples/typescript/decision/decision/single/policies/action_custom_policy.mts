import {
  DecisionClient,
  type Decision,
  type DecisionPolicy,
  type DecisionRequest,
} from "../../../../../../packages/typescript/laix/src/index.ts";

class AlwaysWait implements DecisionPolicy {
  readonly name = "always-wait";
  readonly version = "1.0";

  decide(_request: DecisionRequest): Decision[] {
    return [
      {
        verb: "wait",
        confidence: 0.5,
        reasonCode: "policy_rule",
        rationale: "this policy always waits",
      },
    ];
  }
}

const layer = new DecisionClient({ policy: new AlwaysWait() });
const decision = layer.decide({
  subject: "one decision",
  at: "2026-11-01T10:00:00Z",
})[0]!;

console.log(decision.verb, decision.reasonCode);
