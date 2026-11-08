import {
  DecisionClient,
  SafetyConstrainedPolicy,
} from "../../../../packages/typescript/laix/src/index.ts";
import type { DecisionRequest } from "../../../../packages/typescript/laix/src/index.ts";

const client = new DecisionClient();
client.registerPolicy("safety", new SafetyConstrainedPolicy());
client.usePolicy("safety");

const request: DecisionRequest = {
  subject: "leaking sink",
  at: "2026-11-01T10:00:00Z",
  attributes: {
    risk_limit: 0.2,
    options: [
      { id: "valve", benefit: 0.9, risk: 0.1 },
      { id: "hit-pipe", benefit: 1.0, risk: 0.9 },
    ],
  },
};

const [decision] = client.decide(request);
console.log(
  client.status().registered.join(","),
  decision.verb,
  decision.actionId,
);
