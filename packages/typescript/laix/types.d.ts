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
  export type Severity = "critical" | "high" | "medium" | "low" | "info";
  export type OutcomeResult = "helped" | "neutral" | "hurt" | "unknown";
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

  export interface AttentionDecision {
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

  export interface AttentionOutcome {
    candidateId: string;
    verb: Verb;
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
    kind?: string;
    quote?: string;
    confidence?: number;
    source?: string;
  }

  export interface AuditEvent {
    at: string;
    actor: string;
    event: string;
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
  export interface Policy {
    name: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class Layer {
    constructor(options?: { policy?: Policy });
    registerPolicy(name: string, policy: Policy): void;
    usePolicy(name: string): void;
    decide(request: DecisionRequest): Decision[];
    stream(options?: {
      streamId?: string;
      capacity?: number;
      onFull?: FullPolicy;
      late?: LatePolicy;
      cooldownMs?: number;
      hysteresisMs?: number;
      dedupeMs?: number;
      maxDecisionsPerWindow?: number;
      budgetWindowMs?: number;
      latencySamples?: number;
      trace?: boolean;
      recorder?: (decision: Decision) => void;
      clock?: () => Date;
      idFactory?: () => string;
    }): StreamSession;
    status(): Record<string, unknown>;
    explain(decision: Decision): Record<string, unknown>;
  }

  export interface DecisionRequest {
    subject: string;
    at: string;
    signals?: Signal[];
    context?: Context;
    situation?: Situation;
    options?: ActionOption[];
    attributes?: Record<string, unknown>;
    confidence?: number;
    confidenceSource?: string;
    calibrated?: boolean;
    deadline?: string | null;
    validUntil?: string | null;
    eventId?: string;
    target?: TargetMode;
    recipients?: string[];
  }
  export interface Decision {
    verb: Verb;
    confidence: number;
    reasonCode: string;
    rationale: string;
    decisionId?: string;
    situationId?: string;
    policyVersion?: string;
    actionId?: string | null;
    evidence?: EvidenceRef[];
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
    confidenceSource?: string;
    calibrated?: boolean;
    attributes?: Record<string, unknown>;
    alternatives?: Array<Record<string, unknown>>;
    streamId?: string;
    eventTime?: string | null;
    deadline?: string | null;
    validUntil?: string | null;
    supersedes?: string | null;
    revision?: number;
    status?: "final" | "provisional" | "superseded";
    target?: TargetMode;
    recipients?: string[];
  }
  export interface DecisionProblem {
    subject: string;
    at: string;
    situation?: unknown;
    options: ActionOption[];
    signals?: unknown[];
    context?: unknown;
    attributes: Record<string, unknown>;
  }
  export interface Plan {
    verb: Verb;
    confidence: number;
    reasonCode: string;
    rationale: string;
    actionId?: string | null;
    intent?: Intent | null;
    requiresApproval?: boolean;
    reversible?: boolean;
    undoHint?: string | null;
    score?: number | null;
    alternatives?: Array<Record<string, unknown>>;
    attributes?: Record<string, unknown>;
  }
  export interface DecisionEngine {
    solve(problem: DecisionProblem): Plan;
  }
  export class EnginePolicy {
    readonly name: string;
    readonly engine: DecisionEngine;
    constructor(engine: DecisionEngine, name?: string);
    decide(request: DecisionRequest): Decision[];
  }
  export function toProblem(request: DecisionRequest): DecisionProblem;
  export function toDecision(
    plan: Plan,
    request: DecisionRequest,
    options?: { decisionId?: string; traceId?: string; policyVersion?: string },
  ): Decision;

  export type CausalMethod = "difference-in-means" | "inverse-propensity";
  export interface CausalObservation {
    decisionId: string;
    arm: string;
    outcome: number;
    propensity?: number | null;
    context?: Record<string, unknown>;
  }
  export interface CausalEffect {
    treatment: string;
    control: string;
    estimate: number;
    treated: number;
    controlSize: number;
    method: CausalMethod;
    standardError?: number;
    ciLow?: number;
    ciHigh?: number;
  }
  export class CausalLedger {
    records: CausalObservation[];
    add(
      decisionId: string,
      options: {
        arm: string;
        outcome: number;
        propensity?: number | null;
        context?: Record<string, unknown>;
      },
    ): CausalObservation;
    addOutcome(
      outcome: Outcome,
      options: {
        arm: string;
        propensity?: number | null;
        context?: Record<string, unknown>;
        signed?: boolean;
      },
    ): CausalObservation;
    static fromOutcomes(
      outcomes: Outcome[],
      arms: Record<string, string>,
      options?: {
        defaultArm?: string;
        propensities?: Record<string, number>;
        contexts?: Record<string, Record<string, unknown>>;
        signed?: boolean;
      },
    ): CausalLedger;
    effect(treatment: string, control: string): CausalEffect;
    effectByContext(
      treatment: string,
      control: string,
      options?: { key?: string },
    ): Record<string, CausalEffect>;
  }

  export type CommitmentStatus = "open" | "done" | "cancelled";
  export const COMMITMENT_STATUSES: readonly CommitmentStatus[];
  export interface Commitment {
    id: string;
    subject: string;
    due?: string | null;
    status?: CommitmentStatus;
    dependsOn?: string[];
    priority?: number;
    payload?: Record<string, unknown>;
  }
  export function commitmentDue(commitment: Commitment, now: Date): boolean;
  export class CommitmentLedger {
    constructor(commitments?: Commitment[]);
    add(commitment: Commitment): Required<Commitment>;
    get(commitmentId: string): Required<Commitment>;
    complete(commitmentId: string): Required<Commitment>;
    cancel(commitmentId: string): Required<Commitment>;
    open(): Required<Commitment>[];
    due(now: Date): Required<Commitment>[];
    next(now?: Date): Required<Commitment> | null;
    nextActionable(now?: Date): Required<Commitment> | null;
    blockedOpen(): Required<Commitment>[];
    blocked(commitment: Commitment): boolean;
    toDict(): { commitments: Commitment[] };
    static fromDict(payload: { commitments?: Commitment[] }): CommitmentLedger;
  }
  export interface CommitmentStore {
    save(key: string, ledger: CommitmentLedger): void;
    load(key: string): CommitmentLedger | null;
    delete(key: string): void;
  }
  export interface CommitmentFiles {
    join(directory: string, name: string): string;
    read(path: string): string | null;
    write(path: string, text: string): void;
    remove(path: string): void;
  }
  export class InMemoryCommitmentStore implements CommitmentStore {
    save(key: string, ledger: CommitmentLedger): void;
    load(key: string): CommitmentLedger | null;
    delete(key: string): void;
  }
  export class FileCommitmentStore implements CommitmentStore {
    readonly directory: string;
    constructor(directory: string, files: CommitmentFiles);
    save(key: string, ledger: CommitmentLedger): void;
    load(key: string): CommitmentLedger | null;
    delete(key: string): void;
  }

  export type RiskAttitude = "neutral" | "averse" | "seeking";
  export const RISK_ATTITUDES: readonly RiskAttitude[];
  export interface UtilityWeights {
    benefit?: number;
    cost?: number;
    risk?: number;
    interruption?: number;
    latency?: number;
  }
  export interface UtilityOptions {
    weights?: UtilityWeights;
    riskAttitude?: RiskAttitude;
    maxRisk?: number;
    maxCost?: number | null;
    maxLatencyMs?: number | null;
  }
  export class UtilityModel {
    readonly weights: Required<UtilityWeights>;
    readonly riskAttitude: RiskAttitude;
    readonly maxRisk: number;
    readonly maxCost: number | null;
    readonly maxLatencyMs: number | null;
    constructor(options?: UtilityOptions);
    feasible(option: ActionOption): boolean;
    score(option: ActionOption): number;
  }
  export class UtilityEngine implements DecisionEngine {
    readonly name: string;
    readonly model: UtilityModel;
    constructor(model?: UtilityModel);
    solve(problem: DecisionProblem): Plan;
  }

  export interface MdpTransition {
    state: string;
    action: string;
    nextState: string;
    probability?: number;
    reward?: number;
  }
  export interface MdpModelOptions {
    states: string[];
    actions: string[];
    transitions: MdpTransition[];
    start: string;
    discount?: number;
    horizon?: number | null;
  }
  export class MdpModel {
    readonly states: string[];
    readonly actions: string[];
    readonly transitions: Required<MdpTransition>[];
    readonly start: string;
    readonly discount: number;
    readonly horizon: number | null;
    constructor(options: MdpModelOptions);
    outgoing(state: string, action: string): Required<MdpTransition>[];
    actionsFor(state: string): string[];
  }
  export function valueIteration(
    model: MdpModel,
    options?: { horizon?: number | null; tolerance?: number; maxIterations?: number },
  ): Record<string, number>;
  export function actionValues(
    model: MdpModel,
    state: string,
    values?: Record<string, number>,
  ): Array<[string, number]>;
  export class MDPEngine implements DecisionEngine {
    readonly name: string;
    readonly model: MdpModel;
    readonly state: string;
    constructor(model: MdpModel, options?: { state?: string });
    solve(problem: DecisionProblem): Plan;
  }
  export function planActions(model: MdpModel, state?: string): string[];

  export interface CalibrationSample {
    confidence: number;
    correct: boolean;
    policy?: string;
  }
  export interface CalibrationBin {
    lower: number;
    upper: number;
    predicted: number;
    observed: number;
    count: number;
  }
  export class CalibrationReport {
    readonly samples: number;
    readonly accuracy: number;
    readonly expected: number;
    readonly error: number;
    readonly bins: CalibrationBin[];
    readonly policy: string;
    readonly smoothing: number;
    adjust(confidence: number): number;
    toDict(): Record<string, unknown>;
  }
  export function calibrationReport(
    samples: CalibrationSample[],
    options?: { bins?: number; policy?: string; smoothing?: number },
  ): CalibrationReport;
  export function calibrationByPolicy(
    samples: CalibrationSample[],
    options?: { bins?: number; smoothing?: number },
  ): Record<string, CalibrationReport>;
  export function samplesFromOutcomes(
    outcomes: Outcome[],
    confidences: Record<string, number>,
    options?: { policies?: Record<string, string> },
  ): CalibrationSample[];

  export type Transition = [string, string, string, number];
  export interface LearnedTransition {
    state: string;
    action: string;
    probabilities: Record<string, number>;
    expectedReward: number;
    count: number;
  }
  export class ModelLearner {
    readonly prior: number;
    history: Array<[number, boolean]>;
    constructor(options?: { prior?: number });
    readonly bestScore: number | null;
    observe(state: string, action: string, nextState: string, reward: number): void;
    transitionProbabilities(state: string, action: string): Record<string, number>;
    expectedReward(state: string, action: string): number;
    learned(): LearnedTransition[];
    evaluate(validation: Transition[]): number;
    commit(validation: Transition[]): boolean;
    snapshot(): Record<string, unknown>;
    restore(snapshot: Record<string, unknown>): void;
    toMdpModel(options?: {
      states?: string[];
      actions?: string[];
      start?: string;
      discount?: number;
      horizon?: number | null;
    }): MdpModel;
  }

  export interface PomdpTransition {
    state: string;
    action: string;
    nextState: string;
    probability?: number;
    reward?: number;
  }
  export interface ObservationProbability {
    nextState: string;
    action: string;
    observation: string;
    probability?: number;
  }
  export interface PomdpModelOptions {
    states: string[];
    actions: string[];
    observations: string[];
    transitions: PomdpTransition[];
    observationTable: ObservationProbability[];
    discount?: number;
    horizon?: number;
  }
  export type BeliefState = Record<string, number>;
  export class PomdpModel {
    readonly states: string[];
    readonly actions: string[];
    readonly observations: string[];
    readonly transitions: Required<PomdpTransition>[];
    readonly observationTable: Required<ObservationProbability>[];
    readonly discount: number;
    readonly horizon: number;
    constructor(options: PomdpModelOptions);
    transitionRows(state: string, action: string): Required<PomdpTransition>[];
    observationRows(nextState: string, action: string): Required<ObservationProbability>[];
    actionAvailable(state: string, action: string): boolean;
  }
  export function normalizeBelief(belief: BeliefState, states: string[]): BeliefState;
  export function beliefFromState(state: string, states: string[]): BeliefState;
  export function beliefUpdate(
    model: PomdpModel,
    belief: BeliefState,
    action: string,
    observation: string,
  ): BeliefState;
  export function observationProbability(
    model: PomdpModel,
    belief: BeliefState,
    action: string,
    observation: string,
  ): number;
  export function beliefEntropy(belief: BeliefState): number;
  export function pomdpValue(
    model: PomdpModel,
    belief: BeliefState,
    options?: { horizon?: number },
  ): number;
  export interface PlannerComparison {
    pomdp: number;
    mdp: number;
    gap: number;
    state: string;
  }
  export function comparePomdpToMdp(
    pomdp: PomdpModel,
    mdp: MdpModel,
    belief: BeliefState,
    options?: { horizon?: number },
  ): PlannerComparison;
  export class POMDPEngine implements DecisionEngine {
    readonly name: string;
    readonly model: PomdpModel;
    readonly belief: BeliefState;
    constructor(model: PomdpModel, options?: { belief?: BeliefState });
    solve(problem: DecisionProblem): Plan;
  }
  export interface ActionOption {    id: string;
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
    id?: string;
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
    decide(request: DecisionRequest): Decision[];
  }
  export class SafetyConstrainedPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class ReplanningPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class AllocationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class NegotiationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class PreferenceElicitationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class VerificationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }
  export class EscalationPolicy implements Policy {
    name: string;
    version: string;
    decide(request: DecisionRequest): Decision[];
  }

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
  export class RulePolicy {
    readonly name: string;
    readonly rules: Rule[];
    readonly fallback: Rule;
    constructor(rules: Rule[], options?: { name?: string; fallback?: Rule });
    decide(request: DecisionRequest): Decision[];
  }
  export class TargetedPolicy {
    readonly name: string;
    constructor(
      policy: { decide(request: DecisionRequest): Decision[] },
      options?: { target?: "request" | TargetMode; recipients?: string[] },
    );
    decide(request: DecisionRequest): Decision[];
  }
  export class PlanningPolicy implements Policy {
    readonly name: string;
    readonly ledger: CommitmentLedger;
    constructor(ledger: CommitmentLedger);
    decide(request: DecisionRequest): Decision[];
  }
  export interface GroupPolicyOptions {
    target?: TargetMode;
    recipients?: string[];
    privateAttributes?: string[];
    privateEvidence?: string[];
    rationale?: string;
    undoHint?: string;
  }
  export class GroupPolicy implements Policy {
    readonly name: string;
    readonly policy: { decide(request: DecisionRequest): Decision[] };
    readonly target: TargetMode;
    readonly recipients: string[];
    constructor(
      policy: { decide(request: DecisionRequest): Decision[] },
      options?: GroupPolicyOptions,
    );
    decide(request: DecisionRequest): Decision[];
  }
  export interface PolicyLike {
    decide(request: DecisionRequest): Decision[];
  }
  export function simulate(policy: PolicyLike, requests: DecisionRequest[]): Decision[][];
  export interface ShadowDifference {
    request: DecisionRequest;
    primary: Decision[];
    shadow: Decision[];
  }
  export class ShadowPolicy implements Policy {
    readonly name: string;
    readonly primary: PolicyLike;
    readonly shadow: PolicyLike;
    differences: ShadowDifference[];
    constructor(primary: PolicyLike, shadow: PolicyLike, name?: string);
    decide(request: DecisionRequest): Decision[];
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
    learn(outcomes: Outcome[], armOf: (decisionId: string) => string): number;
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
    decide(request: DecisionRequest): Decision[];
    record(armId: string, reward: number): Arm;
    learn(outcomes: Outcome[], armOf: (decisionId: string) => string): number;
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
  export interface OutcomeStore {
    add(outcome: Outcome): Outcome;
    forDecision(decisionId: string): Outcome[];
    all(): Outcome[];
    summary(): Record<string, unknown>;
  }
  export class OutcomeLedger implements OutcomeStore {
    records: Outcome[];
    tolerance: number;
    add(outcome: Outcome): Outcome;
    forDecision(decisionId: string): Outcome[];
    all(): Outcome[];
    summary(): Record<string, unknown>;
    byMetric(): Record<string, Record<string, number>>;
    toDict(): Record<string, unknown>;
  }
  export function rewardForLabel(label: string): number | null;

  export interface SkillCall { capability: string; args?: Record<string, unknown>; traceId?: string; }
  export interface ApprovalRequest { decisionId: string; actionName: string; rationale?: string; risk?: number; reversible?: boolean; evidence?: string[]; }
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
    constructor(detectors?: Detector[], options?: { budget?: Budget; policy?: ResourceScheduler });
    register(detector: Detector): void;
    perceive(event: PerceptionEvent, uncertainty?: number): PerceptionFrame;
    feed(events: PerceptionEvent[], uncertainty?: number): PerceptionFrame[];
    latest: PerceptionFrame | null;
  }
  export interface Budget { maxDeepCalls?: number; maxCost?: number; maxLatencyMs?: number; }
  export interface SensingOption { name: string; tier?: "cheap" | "deep"; cost?: number; latencyMs?: number; informationGain?: number; }
  export class ResourceScheduler {
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
  export interface StreamCheckpointStore {
    save(key: string, snapshot: Record<string, unknown>): void;
    load(key: string): Record<string, unknown> | null;
    delete(key: string): void;
  }
  export interface CheckpointFiles {
    join(directory: string, name: string): string;
    read(path: string): string | null;
    write(path: string, text: string): void;
    remove(path: string): void;
  }
  export class InMemoryStreamCheckpointStore implements StreamCheckpointStore {
    save(key: string, snapshot: Record<string, unknown>): void;
    load(key: string): Record<string, unknown> | null;
    delete(key: string): void;
  }
  export class FileStreamCheckpointStore implements StreamCheckpointStore {
    readonly directory: string;
    constructor(directory: string, files: CheckpointFiles);
    save(key: string, snapshot: Record<string, unknown>): void;
    load(key: string): Record<string, unknown> | null;
    delete(key: string): void;
  }
  export class ApprovalRequired extends Error {}
  export class UnknownAction extends Error {}
  export interface ExecutionStep {
    action: ActionOption;
    decision?: Decision;
    actor?: string;
    approver?: string | null;
    context?: Record<string, unknown>;
    idempotencyKey?: string;
    compensate?: (receipt: Receipt) => Record<string, unknown>;
  }
  export interface ExecutionSagaResult {
    completed: string[];
    compensated: string[];
    receipts: Receipt[];
    error?: string | null;
    toDict(): Record<string, unknown>;
  }
  export class ExecutionBridge {
    constructor(options?: { handlers?: Record<string, (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>>; undoHandlers?: Record<string, (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>> });
    register(name: string, handler: (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>, undo?: (action: ActionOption, context: Record<string, unknown>) => Record<string, unknown>): void;
    canUndo(name: string): boolean;
    runSteps(steps: ExecutionStep[], options?: { actor?: string }): ExecutionSagaResult;
    execute(decision: Decision, options: { action: ActionOption | null; actor: string; approver?: string | null; context?: Record<string, unknown>; idempotencyKey?: string }): Receipt;
    cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt;
    undo(receiptId: string, options: { actor: string }): Receipt;
    markUnknown(receiptId: string, options: { actor: string; reason?: string }): Receipt;
    reconcile(
      receiptId: string,
      options: { actor: string; status: "executed" | "failed" | "unknown"; detail?: Record<string, unknown> },
    ): Receipt;
  }
  export class DecisionRuntime {
    constructor(options?: { state?: ExperienceState; bridge?: ExecutionBridge; outcomes?: OutcomeLedger; resources?: ResourceScheduler });
    decide(situation: unknown, options: unknown[], attributes?: Record<string, unknown>): Decision & { decisionId: string };
    execute(decision: Decision, options: { actor: string; approver?: string | null; context?: Record<string, unknown>; action?: ActionOption | null }): Receipt;
    cancel(receiptId: string, options: { actor: string; reason?: string }): Receipt;
    undo(receiptId: string, options: { actor: string }): Receipt;
    measure(decisionId: string, options: { metric: string; before: number; after: number; attributed?: boolean; direction?: Outcome["direction"]; note?: string }): Outcome;
    trace(decisionId: string): Trace;
  }
  export type SagaForward = () => Record<string, unknown>;
  export type SagaCompensate = () => Record<string, unknown>;
  export interface SagaStep {
    name: string;
    forward: SagaForward;
    compensate?: SagaCompensate;
  }
  export interface SagaResult {
    completed: string[];
    compensated: string[];
    error?: string | null;
  }
  export class Saga {
    run(steps: SagaStep[]): SagaResult;
  }

  export type Step = (state: string, action: string) => [string, number];
  export type RandomStep = (
    state: string,
    action: string,
    rng: () => number,
  ) => [string, number];
  export interface SimulationStep {
    step: number;
    state: string;
    action: string | null;
    reward: number;
    nextState: string;
  }
  export interface SimulationResult {
    scenario: string;
    steps: SimulationStep[];
    totalReward: number;
    finalState: string;
  }
  export interface SimulatorOptions {
    start: string;
    horizon?: number;
    name?: string;
    seed?: number;
    randomStep?: RandomStep;
  }
  export class Simulator {
    readonly step: Step;
    readonly actions: string[];
    readonly start: string;
    readonly horizon: number;
    readonly name: string;
    readonly seed: number | undefined;
    readonly randomStep: RandomStep | undefined;
    constructor(step: Step, actions: string[], options: SimulatorOptions);
    run(engine: DecisionEngine): SimulationResult;
    static fromMdp(
      model: MdpModel,
      options?: { start?: string; seed?: number },
    ): Simulator;
  }
  export interface Scenario {
    name: string;
    simulator: Simulator;
    optimum?: number | null;
  }
  export interface EngineScore {
    engine: string;
    scenario: string;
    totalReward: number;
    steps: number;
    optimalityGap: number | null;
  }
  export class SimulationReport {
    readonly rows: EngineScore[];
    constructor(rows: EngineScore[]);
    summary(): Record<string, { runs: number; meanReward: number; meanGap: number }>;
    best(): string | null;
    toDict(): Record<string, unknown>;
  }
  export function compareEngines(
    engines: Record<string, DecisionEngine>,
    scenarios: Scenario[],
  ): SimulationReport;
  export function seededScenarios(
    seed: number,
    options?: { count?: number; horizon?: number; actions?: string[] },
  ): Scenario[];

  export class FixedActionEngine implements DecisionEngine {
    readonly action: string;
    constructor(action: string);
    solve(problem: DecisionProblem): Plan;
  }
  export function runEngineBench(horizon?: number): SimulationReport;

  export type DecisionStatus = "final" | "provisional" | "superseded";
  export type TargetMode = "one" | "some" | "all" | "peer" | "gather";
  export const TARGET_MODES: readonly TargetMode[];
  export interface DeadLetter {
    raw: string;
    error: string;
    at: string;
  }
  export class DeadLetterQueue {
    readonly limit: number;
    constructor(limit?: number);
    add(raw: string, error: unknown): void;
    errorHandler(): (raw: string, error: unknown) => void;
    all(): DeadLetter[];
    clear(): void;
    readonly length: number;
  }
  export interface SourceOptions {
    onError?: (raw: string, error: unknown) => void;
    strict?: boolean;
  }
  export function fromQueue<T>(queue: AsyncIterable<T | null>): AsyncIterable<T>;
  export function fromSync<T>(items: Iterable<T>): AsyncIterable<T>;
  export function fromNdjson(
    lines: AsyncIterable<string> | Iterable<string>,
    options?: SourceOptions,
  ): AsyncIterable<DecisionRequest>;
  export function fromSse(
    lines: AsyncIterable<string> | Iterable<string>,
    options?: SourceOptions,
  ): AsyncIterable<DecisionRequest>;
  export function prometheus(stats: StreamStats, prefix?: string): string;
  export interface StreamBenchResult {
    decisions: Decision[];
    elapsedMs: number;
    throughputPerSecond: number;
    stats: Record<string, number>;
  }
  export function runStreamBench(
    session: StreamSession,
    requests: Iterable<DecisionRequest>,
  ): StreamBenchResult;
  export type FullPolicy = "latest_wins" | "drop_oldest" | "drop_newest";
  export type LatePolicy = "drop" | "accept";
  export interface WindowBatch {
    start: Date;
    end: Date;
    events: DecisionRequest[];
  }
  export class TumblingWindow {
    readonly windowMs: number;
    readonly late: LatePolicy;
    constructor(windowMs: number, options?: { late?: LatePolicy });
    readonly pending: number;
    add(event: DecisionRequest): WindowBatch[];
    flush(): WindowBatch[];
  }
  export const DECISION_STATUSES: readonly DecisionStatus[];
  export const FULL_POLICIES: readonly FullPolicy[];
  export const LATE_POLICIES: readonly LatePolicy[];
  export class StreamStats {
    observed: number;
    decided: number;
    late: number;
    throttled: number;
    dropped: number;
    expired: number;
    suppressed: number;
    shed: number;
    duplicates: number;
    refineTimeouts: number;
    provisional: number;
    revised: number;
    latencyP50: number;
    latencyP95: number;
    latencyP99: number;
    snapshot(): Record<string, number>;
    copy(): StreamStats;
  }
  export class ManualClock {
    now: Date;
    constructor(now?: Date);
    set(value: Date): void;
  }
  export class StreamSession {
    constructor(
      decide: (request: DecisionRequest) => Decision[],
      options?: {
        streamId?: string;
        capacity?: number;
        onFull?: FullPolicy;
        late?: LatePolicy;
        cooldownMs?: number;
        hysteresisMs?: number;
        dedupeMs?: number;
        maxDecisionsPerWindow?: number;
        budgetWindowMs?: number;
        latencySamples?: number;
        trace?: boolean;
        recorder?: (decision: Decision) => void;
        clock?: () => Date;
        idFactory?: () => string;
      },
    );
    readonly streamId: string;
    readonly closed: boolean;
    readonly pending: number;
    readonly stats: StreamStats;
    save(store: StreamCheckpointStore, key: string): void;
    resume(store: StreamCheckpointStore, key: string): boolean;
    observe(request: DecisionRequest, options?: { status?: DecisionStatus; force?: boolean }): Decision[];
    observeWait(request: DecisionRequest, options?: { status?: DecisionStatus; force?: boolean }): Promise<Decision[]>;
    revise(previous: Decision, request: DecisionRequest, options?: { status?: DecisionStatus }): Decision[];
    reviseWith(
      previous: Decision,
      request: DecisionRequest,
      decisions: Decision[],
      options?: { status?: DecisionStatus },
    ): Decision[];
    observeRefined(
      request: DecisionRequest,
      refine: (request: DecisionRequest) => Promise<Decision[]>,
      options?: { status?: DecisionStatus; timeoutMs?: number },
    ): Promise<Decision[]>;
    trace(decisionId: string): Trace;
    replay(requests: Iterable<DecisionRequest>): Decision[];
    snapshot(): Record<string, unknown>;
    restore(snapshot: Record<string, unknown>): void;
    feed(
      events: AsyncIterable<DecisionRequest>,
      options?: { coalesceMs?: number },
    ): AsyncIterableIterator<Decision>;
    feedWindows(
      events: AsyncIterable<DecisionRequest>,
      options: {
        windowMs: number;
        onWindow: (batch: WindowBatch) => DecisionRequest | null;
        late?: LatePolicy;
      },
    ): AsyncIterableIterator<Decision>;
    decisions(): AsyncIterableIterator<Decision>;
    close(): void;
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
  export function compare(cases: Case[], decide: (request: unknown) => Decision[], fields?: string[]): Report;
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

  export const SCHEMA_VERSION: string;
  export const POLICY_VERSION: string;
  export const VERBS: Verb[];
  export const PHASES: string[];
  export function clamp(value: number, low?: number, high?: number): number;
  export function confidenceBand(value: number): "low" | "medium" | "high";
  export function iso(value?: Date): string;
  export function newId(prefix: string): string;
