/**
 * LAIX attention — a UI-free timing policy for wait / observe / guide / ask / act / verify / escalate.
 *
 * This is the TypeScript implementation of the canonical LAIX attention contract.
 * It is a port of the Python policy, validated against the same 23 vectors.
 * `guide` is the canonical verb; `notify` is a delivery mode, not an action.
 *
 * The policy is deterministic: same context + signals => same decisions, scores and trace ids.
 * It reads no clock, performs no I/O and names no app.
 */

import type { Escalation, Intent, Verb } from "../contracts.ts";

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type OutcomeResult = "helped" | "neutral" | "hurt" | "unknown";
export type FeedbackState = "accepted" | "dismissed" | "snoozed" | "wrong" | "assigned";

export interface SignalFeedback {
  state: FeedbackState;
  at?: string;
  until?: string;
  note?: string;
}

export interface Signal {
  id: string;
  kind: string;
  title?: string;
  detail?: string;
  severity?: Severity;
  confidence?: number;
  due?: string | null;
  evidenceRefs?: string[];
  groupKey?: string | null;
  interruptionCost?: number;
  requiresApproval?: boolean;
  intent?: Intent | null;
  reversible?: boolean;
  escalation?: Escalation | null;
}

export type QuietHours = [string, string] | string | null;

export interface SignalContext {
  now: string | Date;
  quietHours?: QuietHours;
  stopped?: boolean;
  minSeverity?: Severity;
  minConfidence?: number;
  mutedKinds?: string[];
  interruptionBudget?: number | null;
  sent?: string[];
  feedback?: Record<string, SignalFeedback>;
  escalateAfterHours?: number | null;
  learned?: Record<string, number>;
  allowAct?: boolean;
}

export interface ScoreBreakdown {
  severity: number;
  due: number;
  confidence: number;
  interruption: number;
  learned: number;
  total: number;
}

export interface SignalAttentionDecision {
  signalId: string;
  verb: Verb;
  score: number;
  reasonCode: string;
  confidence: number;
  deliver: boolean;
  record: boolean;
  requiresApproval: boolean;
  evidenceRefs: string[];
  breakdown: ScoreBreakdown;
  traceId: string;
  intent: Intent | null;
  escalation: Escalation | null;
  costOfWaiting: number;
  reversible: boolean;
  undoHint: "withdraw" | "cancel" | null;
}

export interface SignalAttentionOutcome {
  candidateId: string;
  verb: Verb;
  result: OutcomeResult;
  at: string;
  note?: string;
}

const SEVERITY_RANK: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

const SEVERITY_POINTS: Record<Severity, number> = {
  critical: 60,
  high: 45,
  medium: 30,
  low: 15,
  info: 5,
};

const WAIT_FACTOR: Record<Severity, number> = {
  critical: 2.0,
  high: 1.5,
  medium: 1.0,
  low: 0.5,
  info: 0.25,
};

const BLOCKING_FEEDBACK: Record<string, string> = {
  snoozed: "snoozed",
  wrong: "wrong",
  assigned: "assigned",
  dismissed: "dismissed",
};

function clamp(value: number, low = 0, high = 1): number {
  return Math.max(low, Math.min(high, value));
}

function severityOf(value: Severity | undefined): Severity {
  return value ?? "low";
}

function parseDate(value: string | Date | null | undefined): Date | null {
  if (!value) return null;
  const parsed = value instanceof Date ? value : new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function localMinutes(value: string | Date): number {
  if (typeof value === "string") {
    const match = /T(\d{2}):(\d{2})/.exec(value);
    if (match) return Number(match[1]) * 60 + Number(match[2]);
  }
  const date = value instanceof Date ? value : new Date(value);
  return date.getHours() * 60 + date.getMinutes();
}

function localDate(value: string | Date): string {
  if (typeof value === "string") {
    const match = /^(\d{4}-\d{2}-\d{2})/.exec(value);
    if (match) return match[1];
  }
  const date = value instanceof Date ? value : new Date(value);
  const pad = (item: number) => String(item).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function hoursUntil(due: string | null | undefined, now: string | Date): number | null {
  const target = parseDate(due);
  const current = parseDate(now);
  if (!target || !current) return null;
  return (target.getTime() - current.getTime()) / 3_600_000;
}

function minutesOfDay(value: string): number | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value.trim());
  if (!match) return null;
  return Number(match[1]) * 60 + Number(match[2]);
}

function quietWindow(quiet: QuietHours | undefined): [string, string] | null {
  if (!quiet) return null;
  if (Array.isArray(quiet)) return [quiet[0], quiet[1]];
  const index = quiet.indexOf("-");
  if (index < 0) return null;
  const start = quiet.slice(0, index).trim();
  const end = quiet.slice(index + 1).trim();
  return start && end ? [start, end] : null;
}

/** True inside the window, inclusive on both ends. Bad input is never quiet. */
export function isQuietHours(now: string | Date, quiet?: QuietHours): boolean {
  const window = quietWindow(quiet);
  if (!window) return false;
  const start = minutesOfDay(window[0]);
  const end = minutesOfDay(window[1]);
  if (start === null || end === null) return false;
  const minutes = localMinutes(now);
  return start <= end ? minutes >= start && minutes <= end : minutes >= start || minutes <= end;
}

function dueScore(now: string | Date, due: string | null | undefined): number {
  const hours = hoursUntil(due, now);
  if (hours === null) return 0;
  if (hours < 0) return 30;
  if (hours <= 24) return 20;
  if (hours <= 72) return 12;
  if (hours <= 168) return 6;
  return 0;
}

export function score(signal: Signal, context: SignalContext): ScoreBreakdown {
  const severity = SEVERITY_POINTS[severityOf(signal.severity)] ?? 5;
  const due = dueScore(context.now, signal.due);
  const confidence = clamp(signal.confidence ?? 0.5) * 20;
  const interruption = -clamp(signal.interruptionCost ?? 0) * 20;
  const learned = context.learned?.[signal.kind] ?? 0;
  const total = severity + due + confidence + interruption + learned;
  return { severity, due, confidence, interruption, learned, total };
}

export function costOfWaiting(signal: Signal, context: SignalContext): number {
  const factor = WAIT_FACTOR[severityOf(signal.severity)] ?? 0.25;
  return dueScore(context.now, signal.due) * factor;
}

export function undoHint(verb: Verb, reversible: boolean): "withdraw" | "cancel" | null {
  if (verb === "guide" || verb === "ask") return "withdraw";
  if (verb === "act") return reversible ? "cancel" : null;
  return null;
}

export function dedupeKey(signal: Signal, now: string | Date): string {
  return `${signal.id}:${localDate(now)}`;
}

function fnv1a(value: string): string {
  let hash = 0xcbf29ce484222325n;
  const prime = 0x100000001b3n;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= BigInt(value.charCodeAt(index));
    hash = (hash * prime) & 0xffffffffffffffffn;
  }
  return hash.toString(16).padStart(16, "0");
}

export function traceId(signal: Signal, now: string | Date, verb: Verb): string {
  return `tr-${fnv1a(`${signal.id}|${localDate(now)}|${verb}`).slice(0, 12)}`;
}

function feedbackBlocks(feedback: SignalFeedback | undefined, now: string | Date): string | null {
  if (!feedback || feedback.state === "accepted") return null;
  if (feedback.state === "snoozed") {
    if (!feedback.until) return "snoozed";
    const until = parseDate(feedback.until);
    if (!until) return "snoozed";
    const current = parseDate(now);
    if (!current || until.getTime() > current.getTime()) return "snoozed";
    return null;
  }
  return BLOCKING_FEEDBACK[feedback.state] ?? null;
}

function decideOne(signal: Signal, context: SignalContext, delivered: number): SignalAttentionDecision {
  const breakdown = score(signal, context);
  const severity = severityOf(signal.severity);
  const blocked = feedbackBlocks(context.feedback?.[signal.id], context.now);
  let verb: Verb = "guide";
  let reasonCode = "worth_surfacing";
  let record = true;
  let deliver = true;
  let deliveredNow = delivered;

  if (context.stopped) {
    verb = "wait";
    reasonCode = "kill_switch";
    record = false;
    deliver = false;
  } else if (context.mutedKinds?.includes(signal.kind)) {
    verb = "wait";
    reasonCode = "muted";
    record = false;
    deliver = false;
  } else if (blocked !== null) {
    verb = "wait";
    reasonCode = blocked;
    record = false;
    deliver = false;
  } else if ((signal.confidence ?? 0.5) < (context.minConfidence ?? 0)) {
    verb = "wait";
    reasonCode = "low_confidence";
    record = false;
    deliver = false;
  } else if (SEVERITY_RANK[severity] > SEVERITY_RANK[context.minSeverity ?? "high"]) {
    verb = "wait";
    reasonCode = "below_floor";
    record = false;
    deliver = false;
  } else if (context.sent?.includes(dedupeKey(signal, context.now))) {
    verb = "wait";
    reasonCode = "already_sent";
    record = false;
    deliver = false;
  } else if (isQuietHours(context.now, context.quietHours ?? ["22:00", "06:00"]) && severity !== "critical") {
    verb = "wait";
    reasonCode = "quiet_hours";
    record = true;
    deliver = false;
  } else if (context.interruptionBudget !== null && context.interruptionBudget !== undefined && deliveredNow >= context.interruptionBudget) {
    verb = "wait";
    reasonCode = "budget";
    record = false;
    deliver = false;
  } else if (context.escalateAfterHours !== null && context.escalateAfterHours !== undefined && severity === "critical") {
    const hours = hoursUntil(signal.due, context.now);
    if (hours !== null && -hours > context.escalateAfterHours) {
      verb = "escalate";
      reasonCode = "overdue_escalation";
    }
  } else if (context.allowAct && signal.intent && signal.reversible) {
    verb = "act";
    reasonCode = "act";
  } else {
    deliveredNow += 1;
  }

  return {
    signalId: signal.id,
    verb,
    score: breakdown.total,
    reasonCode,
    confidence: clamp(signal.confidence ?? 0.5),
    deliver,
    record,
    requiresApproval: Boolean(signal.requiresApproval),
    evidenceRefs: signal.evidenceRefs ?? [],
    breakdown,
    traceId: traceId(signal, context.now, verb),
    intent: verb === "act" ? signal.intent ?? null : null,
    escalation: verb === "escalate" ? signal.escalation ?? null : null,
    costOfWaiting: costOfWaiting(signal, context),
    reversible: Boolean(signal.reversible),
    undoHint: undoHint(verb, Boolean(signal.reversible)),
  };
}

/** One decision per signal, in input order. */
export function decideSignalAttention(context: SignalContext, signals: Signal[]): SignalAttentionDecision[] {
  const decisions: SignalAttentionDecision[] = [];
  let delivered = 0;
  for (const signal of signals) {
    const decision = decideOne(signal, context, delivered);
    if (decision.deliver) delivered += 1;
    decisions.push(decision);
  }
  return decisions;
}

/** A bounded outcome learner. A bandit can replace it behind the same method. */
export class SignalAttentionLog {
  private readonly outcomes: SignalAttentionOutcome[] = [];

  constructor(initial: SignalAttentionOutcome[] = []) {
    this.outcomes = [...initial];
  }

  record(outcome: SignalAttentionOutcome): void {
    this.outcomes.push(outcome);
    if (this.outcomes.length > 500) this.outcomes.shift();
  }

  all(): SignalAttentionOutcome[] {
    return [...this.outcomes];
  }

  adjustment(kind: string): number {
    const relevant = this.outcomes.filter(
      (outcome) => outcome.candidateId.startsWith(`${kind}:`) || outcome.candidateId.includes(kind),
    );
    if (relevant.length === 0) return 0;
    let value = 0;
    for (const outcome of relevant.slice(-30)) {
      if (outcome.result === "helped") value += 0.04;
      else if (outcome.result === "hurt") value -= 0.08;
      else if (outcome.result === "neutral") value -= 0.04;
    }
    return Math.max(-0.2, Math.min(0.2, value));
  }

  acceptanceRate(): number {
    const useful = this.outcomes.filter((outcome) => outcome.result === "helped").length;
    return this.outcomes.length ? useful / this.outcomes.length : 0;
  }
}
