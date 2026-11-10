/**
 * The one LAIX entry point: one request in, the same decision shape out.
 *
 * A request carries either signals + context for attention allocation, or a
 * situation + options for action selection. Both use generic rules and return
 * the same Decision.
 */

import { decideSignalAttention, type SignalContext, type Signal } from "../decision/sensing/signals/signal-attention.ts";
import type {
  ActionOption,
  Decision,
  DecisionRequest,
  Situation,
  Verb,
} from "../decision/contracts.ts";
import { DecisionPolicyRegistry, type DecisionPolicy } from "../decision/policies/decision-policy-registry.ts";
import { StreamSession, type StreamSessionOptions } from "./streaming.ts";



const VERB_ORDER: Verb[] = ["wait", "observe", "ask", "guide", "act", "verify", "escalate"];

function clamp(value: number, low = 0, high = 1): number {
  return Math.max(low, Math.min(high, value));
}

function truthy(value: unknown): boolean {
  if (typeof value === "string") {
    return ["1", "true", "yes", "required", "always", "blocked", "on"].includes(value.trim().toLowerCase());
  }
  return Boolean(value);
}

function utility(option: ActionOption): number {
  return (option.expectedBenefit ?? 0.5) - 0.25 * (option.risk ?? 0) - 0.15 * (option.interruptCost ?? 0);
}

function best(options: ActionOption[]): ActionOption | null {
  if (options.length === 0) return null;
  return [...options].sort((a, b) => utility(b) - utility(a) || a.id.localeCompare(b.id))[0];
}

function constraintScore(situation: Situation): number {
  const beliefs = situation.beliefs ?? [];
  const fromBeliefs = beliefs.length ? Math.min(...beliefs.map((item) => item.confidence)) : null;
  const fromAttributes = situation.attributes?.confidence;
  if (typeof fromAttributes === "number") return clamp(fromAttributes);
  return fromBeliefs === null ? 0 : clamp(fromBeliefs);
}

function blockedByConstraint(option: ActionOption, situation: Situation): boolean {
  const limits = new Map<string, number>();
  for (const item of situation.constraints ?? []) {
    if (!item.hard) continue;
    const raw = item.value;
    const numeric = typeof raw === "number" ? raw : Number(raw);
    if (Number.isFinite(numeric)) limits.set(item.kind, item.kind === "interruption" && numeric > 1 ? numeric / 100 : numeric);
  }
  const pairs: Array<[string, number]> = [
    ["latency", option.latencyMs ?? 0],
    ["cost", option.cost ?? 0],
    ["budget", option.cost ?? 0],
    ["risk", option.risk ?? 0],
    ["interruption", option.interruptCost ?? 0],
  ];
  return pairs.some(([kind, amount]) => {
    const limit = limits.get(kind);
    return limit !== undefined && amount > limit;
  });
}

export function decideAction(situation: Situation, options: ActionOption[]): Decision {
  const confidence = constraintScore(situation);
  const uncertainty = typeof situation.attributes?.uncertainty === "number"
    ? clamp(situation.attributes.uncertainty)
    : 1 - confidence;
  const urgency = typeof situation.attributes?.urgency === "number" ? Number(situation.attributes.urgency) : 0.5;
  const deadlineBreached = truthy(situation.attributes?.deadline_breached);
  const safetyBreached = truthy(situation.attributes?.safety_breached);
  const verificationDue = truthy(situation.attributes?.verification_due);
  const needsMoreInfo = truthy(situation.attributes?.needs_more_info);
  const safetyBlocked = (situation.constraints ?? []).some(
    (item) => item.kind === "safety" && item.hard && truthy(item.value),
  );
  const approvalConstraint = (situation.constraints ?? []).some(
    (item) => item.kind === "approval" && truthy(item.value),
  );

  const admitted = safetyBlocked
    ? options.filter((option) => option.verb === "wait")
    : options.filter((option) => !blockedByConstraint(option, situation));
  const byVerb = new Map<Verb, ActionOption[]>();
  for (const verb of VERB_ORDER) byVerb.set(verb, admitted.filter((option) => option.verb === verb));

  let verb: Verb = "wait";
  let chosen: ActionOption | null = null;
  let rationale = "no admissible option; keep observing";

  if (safetyBlocked) {
    rationale = "hard safety constraint blocks action";
  } else if ((deadlineBreached || safetyBreached) && (byVerb.get("escalate") ?? []).length > 0) {
    verb = "escalate";
    chosen = best(byVerb.get("escalate") ?? []);
    rationale = safetyBreached
      ? "a hard safety boundary is already breached"
      : "a hard deadline or commitment is already breached";
  } else if ((needsMoreInfo || uncertainty >= 0.45) && (byVerb.get("observe") ?? []).length > 0) {
    verb = "observe";
    chosen = best(byVerb.get("observe") ?? []);
    rationale = "a cheap check can reduce the uncertainty; look before asking anyone else";
  } else if ((uncertainty >= 0.45 || confidence < 0.55) && (byVerb.get("ask") ?? []).length > 0) {
    verb = "ask";
    chosen = best(byVerb.get("ask") ?? []);
    rationale = "the evidence is thin; ask for a check";
  } else if (verificationDue && (byVerb.get("verify") ?? []).length > 0) {
    verb = "verify";
    chosen = best(byVerb.get("verify") ?? []);
    rationale = "a previous action has an unverified outcome";
  } else if (urgency >= 0.75 && confidence >= 0.8 && (byVerb.get("act") ?? []).length > 0) {
    verb = "act";
    chosen = best(byVerb.get("act") ?? []);
    rationale = "urgency and confidence clear the act thresholds";
  } else if (urgency >= 0.45 && (byVerb.get("guide") ?? []).length > 0) {
    verb = "guide";
    chosen = best(byVerb.get("guide") ?? []);
    rationale = "worth surfacing; the urgency stays below the act threshold";
  } else if ((byVerb.get("wait") ?? []).length > 0) {
    verb = "wait";
    chosen = best(byVerb.get("wait") ?? []);
    rationale = "no higher verb is admissible; keep observing";
  } else if (admitted.length > 0) {
    chosen = best(admitted);
    verb = chosen?.verb ?? "wait";
    rationale = "higher verbs were unavailable; the best admissible option wins";
  }

  const requiresApproval = Boolean(
    chosen && (chosen.requiresApproval || chosen.destructive || approvalConstraint),
  );

  return {
    verb,
    confidence,
    reasonCode: "policy_rule",
    rationale,
    actionId: chosen?.id ?? null,
    requiresApproval,
    score: chosen ? utility(chosen) : null,
    traceId: `tr-${situation.id}`,
    deliver: true,
    record: true,
  };
}

export class DecisionClient {
  private registry = new DecisionPolicyRegistry();
  private policy: DecisionPolicy | null;

  constructor(options: { policy?: DecisionPolicy } = {}) {
    this.policy = options.policy ?? null;
    if (this.policy) this.registry.register(this.policy.name, this.policy);
  }

  registerPolicy(name: string, policy: DecisionPolicy): void {
    this.registry.register(name, policy);
  }

  usePolicy(name: string): void {
    this.policy = this.registry.get(name);
  }

  status(): Record<string, unknown> {
    return { policy: this.policy?.name ?? "built-in", registered: this.registry.names() };
  }

  explain(decision: Decision): Record<string, unknown> {
    return {
      verb: decision.verb,
      reasonCode: decision.reasonCode,
      rationale: decision.rationale,
      confidence: decision.confidence,
      actionId: decision.actionId,
      requiresApproval: decision.requiresApproval,
      score: decision.score,
      policy: decision.policyVersion ?? this.policy?.name ?? "built-in",
    };
  }

  stream(options: StreamSessionOptions = {}): StreamSession {
    return new StreamSession((request) => this.decide(request), options);
  }

  decide(request: DecisionRequest): Decision[] {
    const annotate = (decision: Decision): Decision => ({
      ...decision,
      confidenceSource: request.confidenceSource ?? decision.confidenceSource,
      calibrated: request.calibrated ?? decision.calibrated,
    });
    if (this.policy) {
      return this.policy.decide(request).map((decision: Decision) => annotate({
        verb: decision.verb,
        confidence: decision.confidence,
        reasonCode: decision.reasonCode,
        rationale: decision.rationale,
        actionId: decision.actionId ?? null,
        requiresApproval: decision.requiresApproval ?? false,
        score: decision.score ?? null,
        traceId: decision.traceId ?? "",
        deliver: decision.deliver ?? true,
        record: decision.record ?? true,
        decisionId: decision.decisionId,
        situationId: decision.situationId,
        policyVersion: decision.policyVersion,
        evidence: decision.evidence,
        breakdown: decision.breakdown,
        intent: decision.intent,
        escalation: decision.escalation,
        costOfWaiting: decision.costOfWaiting,
        reversible: decision.reversible,
        undoHint: decision.undoHint,
        createdAt: decision.createdAt,
        confidenceSource: decision.confidenceSource,
        calibrated: decision.calibrated,
        attributes: decision.attributes,
        alternatives: decision.alternatives,
        streamId: decision.streamId,
        eventTime: decision.eventTime,
        deadline: decision.deadline,
        validUntil: decision.validUntil,
        supersedes: decision.supersedes,
        revision: decision.revision,
        status: decision.status,
        target: decision.target,
        recipients: decision.recipients,
      }));
    }
    if (request.situation || request.options?.length) {
      if (!request.situation) throw new Error("action selection needs a situation");
      const attributes = {
        ...(request.situation.attributes ?? {}),
        ...(request.confidence !== undefined ? { confidence: request.confidence } : {}),
        ...(request.confidenceSource ? { confidence_source: request.confidenceSource } : {}),
        ...(request.calibrated ? { calibrated: true } : {}),
      };
      return [annotate(decideAction({ ...request.situation, attributes }, request.options ?? []))];
    }
    if (!request.context) throw new Error("attention allocation needs a context with now");
    return decideSignalAttention(request.context as SignalContext, (request.signals ?? []) as Signal[]).map((decision) => annotate({
      verb: decision.verb,
      confidence: decision.confidence,
      reasonCode: decision.reasonCode,
      rationale: decision.reasonCode,
      actionId: null,
      requiresApproval: decision.requiresApproval,
      score: decision.score,
      traceId: decision.traceId,
      deliver: decision.deliver,
      record: decision.record,
    }));
  }
}
