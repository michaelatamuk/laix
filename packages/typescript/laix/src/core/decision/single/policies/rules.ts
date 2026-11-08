import type { Decision, DecisionRequest, Intent, Verb } from "../../../contracts.ts";

export interface Rule {
  when: Record<string, unknown>;
  verb: Verb;
  reasonCode: string;
  rationale?: string;
  confidence?: number;
  actionId?: string | null;
  requiresApproval?: boolean;
  intent?: Intent | null;
}

function matches(attributes: Record<string, unknown>, when: Record<string, unknown>): boolean {
  for (const [key, expected] of Object.entries(when)) {
    const actual = attributes[key];
    if (expected !== null && typeof expected === "object" && !Array.isArray(expected)) {
      for (const [operator, value] of Object.entries(expected as Record<string, unknown>)) {
        if (operator === "gte" && !(typeof actual === "number" && actual >= Number(value))) return false;
        if (operator === "lte" && !(typeof actual === "number" && actual <= Number(value))) return false;
        if (operator === "in" && !(Array.isArray(value) && value.includes(actual))) return false;
        if (operator === "contains" && !(typeof actual === "string" && actual.includes(String(value)))) return false;
        if (!["gte", "lte", "in", "contains"].includes(operator)) return false;
      }
    } else if (actual !== expected) {
      return false;
    }
  }
  return true;
}

export class RulePolicy {
  readonly name: string;
  readonly rules: Rule[];
  readonly fallback: Rule;

  constructor(rules: Rule[], options: { name?: string; fallback?: Rule } = {}) {
    this.name = options.name ?? "rules.v1";
    this.rules = [...rules];
    this.fallback = options.fallback ?? {
      when: {},
      verb: "wait",
      reasonCode: "no_rule",
      rationale: "no rule matched",
      confidence: 0.5,
    };
  }

  decide(request: DecisionRequest): Decision[] {
    const attributes = { ...(request.attributes ?? {}) };
    const rule = this.rules.find((item) => matches(attributes, item.when)) ?? this.fallback;
    return [
      {
        verb: rule.verb,
        confidence: rule.confidence ?? 0.8,
        reasonCode: rule.reasonCode,
        rationale: rule.rationale ?? rule.reasonCode,
        actionId: rule.actionId ?? null,
        intent: rule.intent ?? null,
        requiresApproval: rule.requiresApproval ?? false,
        policyVersion: this.name,
      },
    ];
  }
}
