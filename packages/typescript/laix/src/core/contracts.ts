export type Verb = "wait" | "observe" | "guide" | "ask" | "act" | "verify" | "escalate";

export const SCHEMA_VERSION = "0.6.1";
export const POLICY_VERSION = "0.6.1";

export const VERBS: Verb[] = ["wait", "observe", "guide", "ask", "act", "verify", "escalate"];
export const PHASES = ["observe", "understand", "decide", "act", "verify", "adapt"] as const;
export type Phase = (typeof PHASES)[number];

export interface EvidenceRef {
  id: string;
  kind?: string;
  quote?: string;
  source?: string;
  confidence?: number;
}

export interface Intent {
  capability: string;
  args?: Record<string, unknown>;
}

export interface Escalation {
  target: string;
  reason?: string;
}

export interface Breakdown {
  severity?: number;
  due?: number;
  confidence?: number;
  interruption?: number;
  learned?: number;
  total?: number;
}

export interface Decision {
  verb: Verb;
  confidence: number;
  reasonCode: string;
  rationale: string;
  decisionId?: string;
  policyVersion?: string;
  actionId?: string | null;
  evidence?: EvidenceRef[];
  requiresApproval?: boolean;
  score?: number | null;
  breakdown?: Breakdown;
  intent?: Intent | null;
  escalation?: Escalation | null;
  costOfWaiting?: number;
  reversible?: boolean;
  undoHint?: string | null;
  traceId?: string;
  deliver?: boolean;
  record?: boolean;
  createdAt?: string;
  confidenceSource?: string;
  calibrated?: boolean;
}

export interface DecisionRequest {
  subject: string;
  at: string;
  signals?: unknown[];
  context?: unknown;
  situation?: Situation;
  options?: Action[];
  attributes?: Record<string, unknown>;
  confidence?: number;
  confidenceSource?: string;
  calibrated?: boolean;
}

export interface Observation {
  id: string;
  at: string;
  source: string;
  kind: string;
  confidence?: number;
  payload?: Record<string, unknown>;
  cost?: number;
  latencyMs?: number;
}

export interface Belief {
  id: string;
  proposition: string;
  confidence: number;
  evidence?: string[];
  updatedAt?: string;
  expiresAt?: string | null;
  source?: string;
}

export interface Goal {
  id: string;
  description: string;
  priority?: number;
  deadline?: string | null;
  done?: boolean;
}

export interface Constraint {
  kind: string;
  value: unknown;
  hard?: boolean;
  note?: string;
}

export interface Action {
  id: string;
  verb: Verb;
  name: string;
  params?: Record<string, unknown>;
  expectedBenefit?: number;
  cost?: number;
  risk?: number;
  latencyMs?: number;
  interruptCost?: number;
  destructive?: boolean;
  reversible?: boolean;
  requiresApproval?: boolean;
}

export interface Situation {
  id: string;
  at: string;
  subject: string;
  phase?: Phase;
  horizon?: string;
  beliefs?: Belief[];
  constraints?: Constraint[];
  goals?: Goal[];
  attributes?: Record<string, unknown>;
}

export interface Outcome {
  id: string;
  decisionId: string;
  metric: string;
  before: number;
  after: number;
  delta: number;
  label: "helped" | "neutral" | "hurt" | "unknown";
  attributed?: boolean;
  direction?: "higher-better" | "lower-better";
  evidence?: Record<string, unknown>;
  measuredAt?: string;
  note?: string;
}

export interface Receipt {
  id: string;
  decisionId: string;
  actionName: string;
  status: "pending" | "approved" | "executed" | "refused" | "failed" | "cancelled" | "undone";
  actor: string;
  detail?: Record<string, unknown>;
  error?: string;
  approvedBy?: string | null;
  previousState?: Record<string, unknown>;
  at?: string;
}

export interface TraceEvent {
  at: string;
  stage: string;
  detail?: Record<string, unknown>;
}

export interface Trace {
  id: string;
  decisionId: string;
  events: TraceEvent[];
}

export function clamp(value: number, low = 0, high = 1): number {
  return Math.max(low, Math.min(high, value));
}

export function confidenceBand(value: number): "low" | "medium" | "high" {
  const score = clamp(value);
  if (score >= 0.8) return "high";
  if (score >= 0.55) return "medium";
  return "low";
}

export function iso(value: Date = new Date()): string {
  return value.toISOString().replace(/\.\d{3}Z$/, "Z");
}

let counter = 0;
export function newId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter.toString(36)}`;
}
