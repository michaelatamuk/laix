/**
 * Type declarations for the `laix` package.
 *
 * The package exposes these declarations for TypeScript consumers. `tsc` would otherwise
 * type-check the implementation source, including its internal narrowing. This declaration
 * file keeps the public contract explicit while Vite still bundles the real package from
 * the package source.
 *
 * It is types only: no runtime code, no second policy.
 */
  export type DecisionAction = "wait" | "observe" | "guide" | "ask" | "act" | "verify" | "escalate";
  export type Severity = "critical" | "high" | "medium" | "low" | "info";
  export type OutcomeResult = "helped" | "no_effect" | "hurt" | "unknown";
  export type FeedbackState = "accepted" | "dismissed" | "snoozed" | "wrong" | "assigned";

  export interface Feedback {
    state: FeedbackState;
    at?: string;
    until?: string;
    note?: string;
  }

  export interface Intent {
    capability: string;
    args?: Record<string, unknown>;
  }

  export interface Escalation {
    target: string;
    reason?: string;
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

  export interface Context {
    now: string | Date;
    quietHours?: QuietHours;
    stopped?: boolean;
    minSeverity?: Severity;
    minConfidence?: number;
    mutedKinds?: string[];
    interruptionBudget?: number | null;
    sent?: string[];
    feedback?: Record<string, Feedback>;
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

  export interface Decision {
    signalId: string;
    action: DecisionAction;
    score: number;
    reason: string;
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

  export interface Outcome {
    candidateId: string;
    action: DecisionAction;
    result: OutcomeResult;
    at: string;
    note?: string;
  }

  export class OutcomeLog {
    constructor(initial?: Outcome[]);
    record(outcome: Outcome): void;
    all(): Outcome[];
    adjustment(kind: string): number;
    acceptanceRate(): number;
  }

  export function decide(context: Context, signals: Signal[]): Decision[];
  export function isQuietHours(now: string | Date, quiet?: QuietHours): boolean;
  export function score(signal: Signal, context: Context): ScoreBreakdown;
  export function costOfWaiting(signal: Signal, context: Context): number;

  export type RecordStatus = "draft" | "approved" | "rejected" | "executed" | "undone";
  export type ApprovalState = "pending" | "approved" | "rejected";

  export interface EvidenceRef {
    id: string;
    kind: string;
    quote: string;
    confidence?: number;
    source?: string;
  }

  export interface AuditEvent {
    at: string;
    actor: string;
    action: string;
    detail: string;
  }

  export interface Approval {
    required: boolean;
    state: ApprovalState;
    by?: string;
    at?: string;
    note?: string;
  }

  export interface Undo {
    available: boolean;
    how?: string;
    at?: string;
  }

  export interface DecisionRecord {
    id: string;
    version: 1;
    title: string;
    summary: string;
    decision: { text: string; confidence: number; rationale?: string };
    evidence: EvidenceRef[];
    alternatives: string[];
    approval: Approval;
    status: RecordStatus;
    createdAt: string;
    updatedAt: string;
    audit: AuditEvent[];
    undo: Undo;
    metadata: Record<string, unknown>;
    hash: string;
  }

  export interface CreateDecisionInput {
    title: string;
    summary?: string;
    decision: string;
    confidence?: number;
    rationale?: string;
    evidence: EvidenceRef[];
    alternatives?: string[];
    requiresApproval?: boolean;
    metadata?: Record<string, unknown>;
  }

  export interface CreateOptions {
    now?: string;
    id?: string;
  }

  export interface ApprovalInput {
    by: string;
    at?: string;
    note?: string;
  }

  export interface UndoInput {
    by: string;
    at?: string;
    reason?: string;
    how?: string;
  }

  export function createDecisionRecord(input: CreateDecisionInput, options?: CreateOptions): DecisionRecord;
  export function approveRecord(record: DecisionRecord, input: ApprovalInput): DecisionRecord;
  export function rejectRecord(record: DecisionRecord, input: ApprovalInput): DecisionRecord;
  export function markExecuted(record: DecisionRecord, input: { by: string; at?: string; note?: string }): DecisionRecord;
  export function undoRecord(record: DecisionRecord, input: UndoInput): DecisionRecord;
  export function verifyRecord(record: DecisionRecord): boolean;
  export function fingerprint(value: unknown): string;
  export function canonical(value: unknown): string;

  export type Verb = "wait" | "observe" | "guide" | "ask" | "act" | "verify" | "escalate";
  export interface LayerDecision {
    verb: Verb;
    confidence: number;
    reasonCode: string;
    rationale: string;
    actionId: string | null;
    requiresApproval: boolean;
    score: number | null;
    traceId: string;
    deliver: boolean;
    record: boolean;
    decisionId?: string;
    policyVersion?: string;
    evidence?: unknown[];
    breakdown?: Record<string, number>;
    intent?: Intent | null;
    escalation?: Escalation | null;
    costOfWaiting?: number;
    reversible?: boolean;
    undoHint?: string | null;
    createdAt?: string;
  }
  export interface Policy {
    name: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class Layer {
    constructor(options?: { policy?: Policy });
    registerPolicy(name: string, policy: Policy): void;
    usePolicy(name: string): void;
    decide(request: DecisionRequest): LayerDecision[];
    status(): Record<string, unknown>;
    explain(decision: LayerDecision): Record<string, unknown>;
  }

  export interface DecisionRequest {
    subject: string;
    at: string;
    signals?: Signal[];
    context?: Context;
    situation?: unknown;
    options?: unknown[];
    attributes?: Record<string, unknown>;
  }
  export interface PolicyDecision {
    verb: Verb;
    confidence: number;
    reasonCode: string;
    rationale: string;
    decisionId?: string;
    policyVersion?: string;
    actionId?: string | null;
    evidence?: unknown[];
    requiresApproval?: boolean;
    score?: number | null;
    breakdown?: Record<string, number>;
    intent?: Intent | null;
    escalation?: Escalation | null;
    costOfWaiting?: number;
    reversible?: boolean;
    undoHint?: string | null;
    traceId?: string;
    deliver?: boolean;
    record?: boolean;
    createdAt?: string;
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
  export interface Receipt {
    id: string;
    decisionId: string;
    actionName: string;
    status: string;
    actor: string;
    detail?: Record<string, unknown>;
    error?: string;
    approvedBy?: string | null;
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

  export class PolicyError extends Error {}
  export class PolicyRegistry {
    register(name: string, policy: Policy): void;
    get(name: string): Policy;
    names(): string[];
  }

  export class ActivePerceptionPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class SafetyConstrainedPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class ReplanningPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class AllocationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class NegotiationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class PreferenceElicitationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class VerificationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }
  export class EscalationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): PolicyDecision[];
  }

  export interface Arm {
    id: string;
    priorMean?: number;
    priorWeight?: number;
    cost?: number;
    risk?: number;
  }
  export class UCBBandit {
    exploration: number;
    constructor(arms?: Arm[], exploration?: number);
    add(arm: Arm): void;
    arms(): Array<Required<Arm>>;
    update(armId: string, reward: number): Arm;
    learn(outcomes: MetricOutcome[], armOf: (decisionId: string) => string): number;
    pulls(armId: string): number;
    mean(armId: string): number;
    score(armId: string): number;
    choose(options?: { maxRisk?: number; budget?: number; exclude?: string[] }): Arm | null;
    toDict(): Record<string, unknown>;
  }
  export class BanditPolicy {
    constructor(bandit: UCBBandit, options?: { maxRisk?: number; budget?: number });
    name: string;
    version: string;
    bandit: UCBBandit;
    decide(request: DecisionRequest): PolicyDecision[];
    record(armId: string, reward: number): Arm;
    learn(outcomes: MetricOutcome[], armOf: (decisionId: string) => string): number;
  }
  export interface MetricOutcome {
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
  export interface OutcomeStore {
    add(outcome: MetricOutcome): MetricOutcome;
    forDecision(decisionId: string): MetricOutcome[];
    all(): MetricOutcome[];
    summary(): Record<string, unknown>;
  }
  export class OutcomeLedger implements OutcomeStore {
    records: MetricOutcome[];
    tolerance: number;
    add(outcome: MetricOutcome): MetricOutcome;
    forDecision(decisionId: string): MetricOutcome[];
    all(): MetricOutcome[];
    summary(): Record<string, unknown>;
    byMetric(): Record<string, Record<string, number>>;
    toDict(): Record<string, unknown>;
  }
  export function rewardForLabel(label: string): number | null;

  export interface SkillCall { capability: string; args?: Record<string, unknown>; traceId?: string; }
  export interface ApprovalRequest { decisionId: string; action: string; rationale?: string; risk?: number; reversible?: boolean; evidence?: string[]; }
  export interface ApprovalDecision { approved: boolean; by?: string; at?: string; note?: string; }
  export interface PlatformEvent { traceId: string; kind: string; at?: string; payload?: Record<string, unknown>; }
  export interface Capability { level: "fast" | "balanced" | "deep"; modalities?: string[]; maxLatencyMs?: number | null; maxCost?: number | null; }
  export interface Platform {
    runSkill(call: SkillCall): unknown;
    cancel(runId: string, reason?: string): boolean;
    requestApproval(request: ApprovalRequest): ApprovalDecision;
    readState(key: string): unknown;
    writeState(key: string, value: unknown): void;
    events(traceId: string): PlatformEvent[];
    capability(level: string): Capability;
  }
  export class InMemoryPlatform implements Platform {
    constructor(options?: { approver?: (request: ApprovalRequest) => ApprovalDecision });
    register(capability: string, handler: (call: SkillCall) => unknown): void;
    runSkill(call: SkillCall): unknown;
    cancel(runId: string, reason?: string): boolean;
    requestApproval(request: ApprovalRequest): ApprovalDecision;
    readState(key: string): unknown;
    writeState(key: string, value: unknown): void;
    events(traceId: string): PlatformEvent[];
    capability(level: string): Capability;
  }

  export type ProposalStatus = "pending" | "approved" | "rejected" | "applied" | "undone";
  export interface Proposal {
    id: string;
    title: string;
    summary: string;
    decisionId?: string;
    actionId?: string | null;
    status?: ProposalStatus;
    createdAt?: string;
    createdBy?: string;
    approvedBy?: string | null;
    approvedAt?: string | null;
    appliedAt?: string | null;
    undoHint?: string | null;
    payload?: Record<string, unknown>;
  }
  export function createProposal(proposal: Proposal): Proposal;
  export function approveProposal(proposal: Proposal, by: string, at?: string): Proposal;
  export function rejectProposal(proposal: Proposal, by: string, at?: string): Proposal;
  export function applyProposal(proposal: Proposal, at?: string): Proposal;
  export function undoProposal(proposal: Proposal, at?: string): Proposal;

  export interface DeliveryReceipt { id: string; decisionId: string; channel: string; status: "delivered" | "skipped" | "failed"; at?: string; detail?: Record<string, unknown>; }
  export interface DeliveryPort { deliver(decision: { decisionId?: string }, message: unknown, options?: { channel?: string }): DeliveryReceipt; }
  export class NullDelivery implements DeliveryPort {
    receipts: DeliveryReceipt[];
    deliver(decision: { decisionId?: string }, message: unknown, options?: { channel?: string }): DeliveryReceipt;
    toDict(): Record<string, unknown>;
  }

  export interface Detector { name: string; tier?: "cheap" | "deep"; cost?: number; latencyMs?: number; informationGain?: number; detect(event: PerceptionEvent): Detection[]; }
  export interface Detection { id: string; detector: string; kind: string; subject: string; at: string; confidence?: number; severity?: string; payload?: Record<string, unknown>; }
  export interface PerceptionEvent { subject: string; at: string; payload?: Record<string, unknown>; }
  export interface PerceptionFrame { subject: string; at: string; detections: Detection[]; allowed: string[]; skipped: Array<{ name: string; reason: string; gain: number }>; uncertainty: number; deepCalls: number; cost: number; }
  export class CallableDetector implements Detector {
    constructor(name: string, handler: (event: PerceptionEvent) => Detection[], options?: { tier?: "cheap" | "deep"; cost?: number; latencyMs?: number; informationGain?: number });
    name: string;
    detect(event: PerceptionEvent): Detection[];
  }
  export class LiveContext {
    constructor(detectors?: Detector[], options?: { budget?: Budget; policy?: ResourcePolicy });
    register(detector: Detector): void;
    perceive(event: PerceptionEvent, uncertainty?: number): PerceptionFrame;
    feed(events: PerceptionEvent[], uncertainty?: number): PerceptionFrame[];
    latest: PerceptionFrame | null;
  }
  export interface Budget { maxDeepCalls?: number; maxCost?: number; maxLatencyMs?: number; }
  export interface SensingOption { name: string; tier?: "cheap" | "deep"; cost?: number; latencyMs?: number; informationGain?: number; }
  export class ResourcePolicy {
    constructor(options?: { minInformationGain?: number });
    schedule(options: SensingOption[], settings?: { budget?: Budget; uncertainty?: number }): Record<string, unknown>;
  }
  export class ExperienceState {
    constructor(subject: string, phase?: string);
    phase: string;
    beliefs: Map<string, Belief>;
    observe(observation: Observation, halfLifeMinutes?: number): Belief | null;
    setBelief(belief: Belief): Belief;
    confidence(ids?: string[]): number;
    advance(phase: string): void;
    snapshot(): Record<string, unknown>;
    static fromSnapshot(payload: Record<string, unknown>): ExperienceState;
  }
  export interface StateStore {
    save(key: string, state: ExperienceState): void;
    load(key: string): ExperienceState | null;
    delete(key: string): void;
  }
  export class InMemoryStateStore implements StateStore {
    save(key: string, state: ExperienceState): void;
    load(key: string): ExperienceState | null;
    delete(key: string): void;
  }
  export class ApprovalRequired extends Error {}
  export class UnknownAction extends Error {}
  export class ExecutionBridge {
    constructor(options?: { handlers?: Record<string, (action: Action, context: Record<string, unknown>) => Record<string, unknown>>; undoHandlers?: Record<string, (action: Action, context: Record<string, unknown>) => Record<string, unknown>> });
    register(name: string, handler: (action: Action, context: Record<string, unknown>) => Record<string, unknown>, undo?: (action: Action, context: Record<string, unknown>) => Record<string, unknown>): void;
    execute(decision: LayerDecision, options: { action: Action | null; actor: string; approver?: string | null; context?: Record<string, unknown> }): Receipt;
    cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt;
    undo(receiptId: string, options: { actor: string }): Receipt;
  }
  export class DecisionRuntime {
    constructor(options?: { state?: ExperienceState; bridge?: ExecutionBridge; outcomes?: OutcomeLedger; resources?: ResourcePolicy });
    decide(situation: unknown, options: unknown[], attributes?: Record<string, unknown>): LayerDecision & { decisionId: string };
    execute(decision: LayerDecision, options: { actor: string; approver?: string | null; context?: Record<string, unknown>; action?: Action | null }): Receipt;
    cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt;
    undo(receiptId: string, options: { actor: string }): Receipt;
    measure(decisionId: string, options: { metric: string; before: number; after: number; attributed?: boolean; direction?: MetricOutcome["direction"]; note?: string }): MetricOutcome;
    trace(decisionId: string): Trace;
  }

  export interface Case { id: string; request: unknown; expected?: Record<string, unknown>[]; }
  export interface Row { caseId: string; expected: Record<string, unknown>[]; actual: Record<string, unknown>[]; mismatches: string[]; passed: boolean; }
  export interface Report {
    rows: Row[];
    fields: string[];
    total: number;
    passed: number;
    failed: number;
    agreementRate: number;
    toDict(): Record<string, unknown>;
  }
  export function compare(cases: Case[], decide: (request: unknown) => PolicyDecision[], fields?: string[]): Report;
  export function loadCases(document: { cases?: Record<string, unknown>[] }): Case[];

  export interface BenchReport {
    total: number;
    passed: number;
    failed: number;
    agreement: number;
    bySuite(): Record<string, { cases: number; passed: number; failed: number; agreement: number }>;
    toDict(): Record<string, unknown>;
  }
  export function runBench(names?: string[]): BenchReport;
  export function suiteNames(): string[];

  export const VERBS: Verb[];
  export const PHASES: string[];
  export function clamp(value: number, low?: number, high?: number): number;
  export function confidenceBand(value: number): "low" | "medium" | "high";
  export function iso(value?: Date): string;
  export function newId(prefix: string): string;
