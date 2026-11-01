/** The eight packaged policy packs behind the same Layer interface. */
import {
  ActivePerceptionPolicy,
  AllocationPolicy,
  EscalationPolicy,
  Layer,
  NegotiationPolicy,
  PreferenceElicitationPolicy,
  ReplanningPolicy,
  SafetyConstrainedPolicy,
  VerificationPolicy,
} from "../../../packages/typescript/laix/src/index.ts";
import type { Policy } from "../../../packages/typescript/laix/src/index.ts";

const at = "2026-11-01T10:00:00Z";
const cases: Array<[Policy, Record<string, unknown>]> = [
  [new ActivePerceptionPolicy(), { uncertainty: 0.8, observations: [{ id: "look-1", information_gain: 0.7, cost: 0.1 }] }],
  [new SafetyConstrainedPolicy(), { risk_limit: 0.2, options: [{ id: "valve", benefit: 0.9, risk: 0.1 }] }],
  [new ReplanningPolicy(), { plans: [{ id: "plan-fast", success_probability: 0.8, cost: 1 }], min_success: 0.7, max_cost: 5 }],
  [new AllocationPolicy(), { budget: 10, requests: [{ id: "a", value: 6, cost: 4 }] }],
  [new NegotiationPolicy(), { offer: 5, reservation: 10, target: 20, round: 1 }],
  [new PreferenceElicitationPolicy(), { uncertainty: 0.8, questions: [{ id: "q2", information_gain: 0.8, cost: 1 }] }],
  [new VerificationPolicy(), { confidence: 0.5, required_confidence: 0.8, checks: [{ id: "api", confidence_gain: 0.8, cost: 1 }] }],
  [new EscalationPolicy(), { severity: 0.9, severity_threshold: 0.8, target: "manager" }],
];

for (const [policy, attributes] of cases) {
  const [decision] = new Layer({ policy }).decide({ subject: "one case", at, attributes });
  console.log(policy.name, decision.verb, decision.reasonCode, decision.actionId);
}
