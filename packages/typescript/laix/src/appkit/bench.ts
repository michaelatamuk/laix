import type { ActionOption } from "../core/contracts.ts";
import { DecisionClient } from "./decision-client.ts";
import type { Decision, DecisionRequest } from "../core/contracts.ts";
import { ActivePerceptionPolicy } from "../core/engines/decision/single/policies/active-perception.ts";
import { AllocationPolicy } from "../core/engines/decision/single/policies/allocation.ts";
import { EscalationPolicy } from "../core/engines/decision/single/policies/escalation.ts";
import { NegotiationPolicy } from "../core/engines/decision/single/policies/negotiation.ts";
import { PreferenceElicitationPolicy } from "../core/engines/decision/single/policies/preference.ts";
import { ReplanningPolicy } from "../core/engines/decision/single/policies/replanning.ts";
import { SafetyConstrainedPolicy } from "../core/engines/decision/single/policies/safety.ts";
import { VerificationPolicy } from "../core/engines/decision/single/policies/verification.ts";

export const AT = "2026-11-01T10:00:00Z";
export const FIELDS = ["verb", "reasonCode", "actionId", "requiresApproval"];

export interface BenchCase {
  id: string;
  request: unknown;
  expected: Record<string, unknown>;
}

export interface Suite {
  name: string;
  description: string;
  policy: () => { decide(request: unknown): Decision[] };
  cases: BenchCase[];
}

export interface BenchRow {
  suite: string;
  case: string;
  expected: Record<string, unknown>;
  actual: Record<string, unknown>;
  mismatches: string[];
  passed: boolean;
}

export interface BenchReport {
  rows: BenchRow[];
  fields: string[];
  total: number;
  passed: number;
  failed: number;
  agreement: number;
  bySuite(): Record<string, { cases: number; passed: number; failed: number; agreement: number }>;
  toDict(): Record<string, unknown>;
}

function request(attributes: Record<string, unknown>): DecisionRequest {
  return { subject: "bench case", at: AT, attributes };
}

function decisionDict(decision: Decision): Record<string, unknown> {
  return {
    verb: decision.verb,
    reasonCode: decision.reasonCode,
    actionId: decision.actionId ?? null,
    requiresApproval: decision.requiresApproval ?? false,
  };
}

function attentionSuite(): Suite {
  const now = new Date("2026-11-01T10:00:00Z");
  const night = new Date("2026-11-01T23:30:00Z");
  const signal = { id: "bill-1", kind: "deadline", title: "Electricity bill due tomorrow", severity: "high", confidence: 0.95, due: "2026-11-02T09:00:00Z" };
  return {
    name: "attention",
    description: "which signal deserves attention now",
    policy: () => new DecisionClient(),
    cases: [
      { id: "attention_bill_day", request: { subject: "bill", at: AT, signals: [signal], context: { now: now.toISOString(), quietHours: ["22:00", "06:00"] } }, expected: { verb: "guide", reasonCode: "worth_surfacing" } },
      { id: "signal_attention_quiet_hours", request: { subject: "bill", at: AT, signals: [signal], context: { now: night.toISOString(), quietHours: ["22:00", "06:00"] } }, expected: { verb: "wait", reasonCode: "quiet_hours" } },
      { id: "attention_dismissed", request: { subject: "bill", at: AT, signals: [signal], context: { now: now.toISOString(), quietHours: null, feedback: { "bill-1": { state: "dismissed" } } } }, expected: { verb: "wait", reasonCode: "dismissed" } },
    ],
  };
}

function actionSuite(): Suite {
  const sink: ActionOption[] = [
    { id: "option-wait", verb: "wait", name: "keep watching", expectedBenefit: 0.1 },
    { id: "option-close-valve", verb: "act", name: "close the valve", expectedBenefit: 0.95, risk: 0.05, reversible: true },
  ];
  const pay: ActionOption[] = [
    { id: "option-wait", verb: "wait", name: "pay later", expectedBenefit: 0.1 },
    { id: "option-pay", verb: "act", name: "pay the bill", expectedBenefit: 0.9, requiresApproval: true },
  ];
  const parcel: ActionOption[] = [
    { id: "option-wait", verb: "wait", name: "keep waiting", expectedBenefit: 0.2 },
    { id: "option-check-tracking", verb: "observe", name: "read the tracking page", expectedBenefit: 0.6 },
    { id: "option-ask-courier", verb: "ask", name: "ask the courier", expectedBenefit: 0.4 },
  ];
  return {
    name: "action",
    description: "which available action to take",
    policy: () => new DecisionClient(),
    cases: [
      { id: "action_sink", request: { subject: "sink", at: AT, situation: { id: "sink-1", at: AT, subject: "sink", beliefs: [{ confidence: 0.95 }], attributes: { urgency: 0.9 } }, options: sink }, expected: { verb: "act", reasonCode: "policy_rule", actionId: "option-close-valve" } },
      { id: "action_payment_approval", request: { subject: "payment", at: AT, situation: { id: "pay-1", at: AT, subject: "payment", beliefs: [{ confidence: 0.95 }], attributes: { urgency: 0.9 } }, options: pay }, expected: { verb: "act", reasonCode: "policy_rule", actionId: "option-pay", requiresApproval: true } },
      { id: "action_check_first", request: { subject: "parcel", at: AT, situation: { id: "parcel-1", at: AT, subject: "parcel", beliefs: [{ confidence: 0.6 }], attributes: { urgency: 0.8, needs_more_info: true } }, options: parcel }, expected: { verb: "observe", reasonCode: "policy_rule", actionId: "option-check-tracking" } },
    ],
  };
}

function suite(name: string, description: string, policy: () => { decide(request: unknown): Decision[] }, cases: BenchCase[]): Suite {
  return { name, description, policy, cases };
}

export function allSuites(): Suite[] {
  return [
    attentionSuite(),
    actionSuite(),
    suite("active-perception", "look before deciding when uncertainty is high", () => new ActivePerceptionPolicy(), [
      { id: "active_perception_look", request: request({ uncertainty: 0.8, observations: [{ id: "look-1", information_gain: 0.7, cost: 0.1 }] }), expected: { verb: "observe", reasonCode: "observe_for_information", actionId: "look-1" } },
      { id: "active_perception_skip", request: request({ uncertainty: 0.1 }), expected: { verb: "wait", reasonCode: "uncertainty_low" } },
    ]),
    suite("safety", "act only inside the hard risk limit", () => new SafetyConstrainedPolicy(), [
      { id: "safety_safe_option", request: request({ risk_limit: 0.2, options: [{ id: "valve", benefit: 0.9, risk: 0.1 }, { id: "hit-pipe", benefit: 1, risk: 0.9 }] }), expected: { verb: "act", reasonCode: "safe_action", actionId: "valve" } },
      { id: "safety_blocked", request: request({ risk_limit: 0.1, options: [{ id: "risky", benefit: 1, risk: 0.9 }] }), expected: { verb: "wait", reasonCode: "no_safe_option" } },
    ]),
    suite("replanning", "choose a replacement plan", () => new ReplanningPolicy(), [
      { id: "replanning_feasible", request: request({ plans: [{ id: "plan-slow", success_probability: 0.95, cost: 10, deadline_risk: 0.1 }, { id: "plan-fast", success_probability: 0.8, cost: 1, deadline_risk: 0.1 }], min_success: 0.7, max_cost: 5 }), expected: { verb: "act", reasonCode: "replan", actionId: "plan-fast" } },
      { id: "replanning_none", request: request({ plans: [{ id: "plan-slow", success_probability: 0.95, cost: 10 }], min_success: 0.99, max_cost: 2 }), expected: { verb: "ask", reasonCode: "no_feasible_plan" } },
    ]),
    suite("allocation", "fund a portfolio under a budget", () => new AllocationPolicy(), [
      { id: "allocation_fund", request: request({ budget: 10, requests: [{ id: "a", value: 6, cost: 4 }, { id: "b", value: 5, cost: 6 }, { id: "c", value: 9, cost: 20 }] }), expected: { verb: "act", reasonCode: "allocate" } },
      { id: "allocation_empty", request: request({ budget: 1, requests: [{ id: "a", value: 6, cost: 4 }] }), expected: { verb: "wait", reasonCode: "nothing_affordable" } },
    ]),
    suite("negotiation", "accept, counter or escalate", () => new NegotiationPolicy(), [
      { id: "negotiation_counter", request: request({ offer: 5, reservation: 10, target: 20, round: 1 }), expected: { verb: "act", reasonCode: "counter_offer", actionId: "counter_offer" } },
      { id: "negotiation_accept", request: request({ offer: 12, reservation: 10, target: 20, round: 1 }), expected: { verb: "act", reasonCode: "accept_offer", actionId: "accept_offer" } },
      { id: "negotiation_round_limit", request: request({ offer: 5, reservation: 10, target: 20, round: 5 }), expected: { verb: "escalate", reasonCode: "round_limit" } },
    ]),
    suite("preference", "ask the best preference question", () => new PreferenceElicitationPolicy(), [
      { id: "preference_ask", request: request({ uncertainty: 0.8, questions: [{ id: "q1", information_gain: 0.2, cost: 1 }, { id: "q2", information_gain: 0.8, cost: 1 }] }), expected: { verb: "ask", reasonCode: "ask_preference", actionId: "q2" } },
      { id: "preference_known", request: request({ uncertainty: 0.1 }), expected: { verb: "act", reasonCode: "preference_known" } },
    ]),
    suite("verification", "confirm that an action worked", () => new VerificationPolicy(), [
      { id: "verification_check", request: request({ confidence: 0.5, required_confidence: 0.8, checks: [{ id: "manual", confidence_gain: 0.2, cost: 1 }, { id: "api", confidence_gain: 0.8, cost: 1 }] }), expected: { verb: "verify", reasonCode: "verify_outcome", actionId: "api" } },
      { id: "verification_no_path", request: request({ confidence: 0.3, required_confidence: 0.8, checks: [] }), expected: { verb: "escalate", reasonCode: "no_verification_path" } },
      { id: "verification_not_needed", request: request({ confidence: 0.95, required_confidence: 0.8, verification_due: false, checks: [] }), expected: { verb: "wait", reasonCode: "verification_not_needed" } },
    ]),
    suite("escalation", "decide when to hand over", () => new EscalationPolicy(), [
      { id: "escalation_target", request: request({ severity: 0.9, severity_threshold: 0.8, target: "manager" }), expected: { verb: "escalate", reasonCode: "escalate_to_target", actionId: "manager" } },
      { id: "escalation_within_limits", request: request({ severity: 0.2, severity_threshold: 0.8, confidence: 0.9 }), expected: { verb: "wait", reasonCode: "within_limits" } },
      { id: "escalation_target_required", request: request({ severity: 0.9, severity_threshold: 0.8 }), expected: { verb: "ask", reasonCode: "target_required" } },
    ]),
  ];
}

export function suiteNames(): string[] {
  return allSuites().map((item) => item.name);
}

export function runBench(names?: string[]): BenchReport {
  const chosen = new Set(names ?? []);
  const suites = allSuites().filter((item) => chosen.size === 0 || chosen.has(item.name));
  const rows: BenchRow[] = [];
  for (const item of suites) {
    const policy = item.policy();
    for (const benchCase of item.cases) {
      const decisions = policy.decide(benchCase.request);
      const actual = decisions.length ? decisionDict(decisions[0]) : {};
      const mismatches = Object.entries(benchCase.expected)
        .filter(([key, want]) => actual[key] !== want)
        .map(([key, want]) => `${key}: ${JSON.stringify(actual[key])} != ${JSON.stringify(want)}`);
      rows.push({ suite: item.name, case: benchCase.id, expected: benchCase.expected, actual, mismatches, passed: mismatches.length === 0 });
    }
  }
  const passed = rows.filter((row) => row.passed).length;
  const report: BenchReport = {
    rows,
    fields: FIELDS,
    total: rows.length,
    passed,
    failed: rows.length - passed,
    agreement: rows.length ? Number((passed / rows.length).toFixed(4)) : 1,
    bySuite() {
      const result: Record<string, { cases: number; passed: number; failed: number; agreement: number }> = {};
      for (const name of [...new Set(rows.map((row) => row.suite))]) {
        const group = rows.filter((row) => row.suite === name);
        const good = group.filter((row) => row.passed).length;
        result[name] = { cases: group.length, passed: good, failed: group.length - good, agreement: group.length ? Number((good / group.length).toFixed(4)) : 1 };
      }
      return result;
    },
    toDict() {
      return { total: rows.length, passed, failed: rows.length - passed, agreement: rows.length ? Number((passed / rows.length).toFixed(4)) : 1, fields: FIELDS, suites: this.bySuite(), rows };
    },
  };
  return report;
}
