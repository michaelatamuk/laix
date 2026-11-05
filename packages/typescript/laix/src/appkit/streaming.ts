import { newId } from "../core/contracts.ts";
import type { Decision, DecisionRequest, Trace } from "../core/contracts.ts";

export const DECISION_STATUSES = ["final", "provisional", "superseded"] as const;
export type DecisionStatus = (typeof DECISION_STATUSES)[number];

export const FULL_POLICIES = ["latest_wins", "drop_oldest", "drop_newest"] as const;
export type FullPolicy = (typeof FULL_POLICIES)[number];

export const LATE_POLICIES = ["drop", "accept"] as const;
export type LatePolicy = (typeof LATE_POLICIES)[number];

export type Decider = (request: DecisionRequest) => Decision[];
export type Refiner = (request: DecisionRequest) => Promise<Decision[]>;
export type Clock = () => Date;
export class StreamStats {
  observed = 0;
  decided = 0;
  late = 0;
  throttled = 0;
  dropped = 0;
  expired = 0;
  suppressed = 0;
  shed = 0;
  duplicates = 0;
  refineTimeouts = 0;
  provisional = 0;
  revised = 0;
  latencyP50 = 0;
  latencyP95 = 0;
  latencyP99 = 0;

  snapshot(): Record<string, number> {
    return {
      observed: this.observed,
      decided: this.decided,
      late: this.late,
      throttled: this.throttled,
      dropped: this.dropped,
      expired: this.expired,
      suppressed: this.suppressed,
      shed: this.shed,
      duplicates: this.duplicates,
      refineTimeouts: this.refineTimeouts,
      provisional: this.provisional,
      revised: this.revised,
      latencyP50: this.latencyP50,
      latencyP95: this.latencyP95,
      latencyP99: this.latencyP99,
    };
  }

  copy(): StreamStats {
    const copy = new StreamStats();
    copy.observed = this.observed;
    copy.decided = this.decided;
    copy.late = this.late;
    copy.throttled = this.throttled;
    copy.dropped = this.dropped;
    copy.expired = this.expired;
    copy.suppressed = this.suppressed;
    copy.shed = this.shed;
    copy.duplicates = this.duplicates;
    copy.refineTimeouts = this.refineTimeouts;
    copy.provisional = this.provisional;
    copy.revised = this.revised;
    copy.latencyP50 = this.latencyP50;
    copy.latencyP95 = this.latencyP95;
    copy.latencyP99 = this.latencyP99;
    return copy;
  }
}

export class ManualClock {
  now: Date;

  constructor(now: Date = new Date()) {
    this.now = now;
  }

  set(value: Date): void {
    this.now = value;
  }
}

export interface StreamSessionOptions {
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
  clock?: Clock;
  idFactory?: () => string;
}

export class StreamSession {
  private streamIdValue: string;
  private readonly decide: Decider;
  private readonly capacity: number;
  private readonly onFull: FullPolicy;
  private readonly late: LatePolicy;
  private readonly cooldownMs: number;
  private readonly hysteresisMs: number;
  private readonly dedupeMs: number;
  private readonly maxDecisions: number | null;
  private readonly budgetWindowMs: number;
  private readonly latencySamples: number;
  private readonly traceEnabled: boolean;
  private readonly recorder: ((decision: Decision) => void) | null;
  private clock: Clock;
  private readonly items: Decision[] = [];
  private waiters: Array<() => void> = [];
  private spaceWaiters: Array<() => void> = [];
  private closedFlag = false;
  private watermark: number | null = null;
  private lastDecision: Date | null = null;
  private lastSignature: Array<[string, string | null]> | null = null;
  private lastSignatureAt: Date | null = null;
  private windowStart: Date | null = null;
  private windowCount = 0;
  private readonly latencies: number[] = [];
  private readonly seen = new Map<string, number>();
  private readonly traces = new Map<string, Trace>();
  private readonly traceByDecision = new Map<string, string>();
  private readonly statsValue = new StreamStats();

  constructor(decide: Decider, options: StreamSessionOptions = {}) {
    const capacity = options.capacity ?? 32;
    if (capacity <= 0) throw new Error("capacity must be positive");
    const onFull = options.onFull ?? "latest_wins";
    if (!FULL_POLICIES.includes(onFull)) throw new Error(`unknown full policy: ${onFull}`);
    const late = options.late ?? "drop";
    if (!LATE_POLICIES.includes(late)) throw new Error(`unknown late policy: ${late}`);
    const cooldownMs = options.cooldownMs ?? 0;
    if (cooldownMs < 0) throw new Error("cooldownMs must be zero or positive");
    const hysteresisMs = options.hysteresisMs ?? 0;
    if (hysteresisMs < 0) throw new Error("hysteresisMs must be zero or positive");
    const dedupeMs = options.dedupeMs ?? 0;
    if (dedupeMs < 0) throw new Error("dedupeMs must be zero or positive");
    const maxDecisions = options.maxDecisionsPerWindow ?? null;
    if (maxDecisions !== null && maxDecisions <= 0) throw new Error("maxDecisionsPerWindow must be positive");
    const budgetWindowMs = options.budgetWindowMs ?? 1000;
    if (budgetWindowMs <= 0) throw new Error("budgetWindowMs must be positive");
    const latencySamples = options.latencySamples ?? 256;
    if (latencySamples <= 0) throw new Error("latencySamples must be positive");

    this.decide = decide;
    this.streamIdValue = options.streamId ?? (options.idFactory ?? (() => newId("STR")))();
    this.capacity = capacity;
    this.onFull = onFull;
    this.late = late;
    this.cooldownMs = cooldownMs;
    this.hysteresisMs = hysteresisMs;
    this.dedupeMs = dedupeMs;
    this.maxDecisions = maxDecisions;
    this.budgetWindowMs = budgetWindowMs;
    this.latencySamples = latencySamples;
    this.traceEnabled = options.trace ?? true;
    this.recorder = options.recorder ?? null;
    this.clock = options.clock ?? (() => new Date());
  }

  get closed(): boolean {
    return this.closedFlag;
  }

  get streamId(): string {
    return this.streamIdValue;
  }

  get pending(): number {
    return this.items.length;
  }

  get stats(): StreamStats {
    return this.statsValue.copy();
  }

  observe(request: DecisionRequest, options: { status?: DecisionStatus; force?: boolean } = {}): Decision[] {
    const decisions = this.admit(request, options.status ?? "final", options.force ?? false, 0, null);
    for (const decision of decisions) this.append(decision);
    return decisions;
  }

  async observeWait(
    request: DecisionRequest,
    options: { status?: DecisionStatus; force?: boolean } = {},
  ): Promise<Decision[]> {
    while (!this.closedFlag && this.items.length >= this.capacity) {
      await new Promise<void>((resolve) => this.spaceWaiters.push(resolve));
    }
    return this.observe(request, options);
  }

  trace(decisionId: string): Trace {
    const traceId = this.traceByDecision.get(decisionId);
    if (!traceId) throw new Error(`unknown decision ${decisionId}`);
    return this.traces.get(traceId)!;
  }

  revise(previous: Decision, request: DecisionRequest, options: { status?: DecisionStatus } = {}): Decision[] {
    const decisions = this.admit(
      request,
      options.status ?? "final",
      true,
      (previous.revision ?? 0) + 1,
      previous.decisionId ?? null,
    );
    for (const decision of decisions) this.append(decision);
    return decisions;
  }

  reviseWith(
    previous: Decision,
    request: DecisionRequest,
    decisions: Decision[],
    options: { status?: DecisionStatus } = {},
  ): Decision[] {
    if (this.closedFlag) throw new Error("stream session is closed");
    const status = options.status ?? "final";
    if (!DECISION_STATUSES.includes(status)) throw new Error(`unknown decision status: ${status}`);
    const revised = decisions.map((item) =>
      this.stamp(item, request, status, (previous.revision ?? 0) + 1, previous.decisionId ?? null),
    );
    if (revised.length) {
      for (const item of revised) this.append(item);
      const now = this.clock();
      this.statsValue.decided += revised.length;
      this.statsValue.revised += revised.length;
      if (status === "provisional") this.statsValue.provisional += revised.length;
      this.lastDecision = now;
      this.lastSignature = revised.map((item) => [item.verb, item.actionId ?? null]);
      this.lastSignatureAt = now;
      this.recordDecisions(revised);
    }
    return revised;
  }

  async observeRefined(
    request: DecisionRequest,
    refine: Refiner,
    options: { status?: DecisionStatus; timeoutMs?: number } = {},
  ): Promise<Decision[]> {
    if (options.timeoutMs !== undefined && options.timeoutMs <= 0) {
      throw new Error("timeoutMs must be positive");
    }
    const first = this.observe(request, { status: options.status ?? "provisional" });
    if (!first.length) return [];
    if (options.timeoutMs === undefined) {
      const refined = await refine(request);
      return [...first, ...this.reviseWith(first[first.length - 1]!, request, refined)];
    }
    const refined = await Promise.race<Decision[] | null>([
      refine(request),
      new Promise<null>((resolve) => setTimeout(() => resolve(null), options.timeoutMs)),
    ]);
    if (refined === null) {
      this.statsValue.refineTimeouts += 1;
      return [
        ...first,
        ...this.reviseWith(first[first.length - 1]!, request, first, { status: "final" }),
      ];
    }
    return [...first, ...this.reviseWith(first[first.length - 1]!, request, refined)];
  }

  replay(requests: Iterable<DecisionRequest>): Decision[] {
    const original = this.clock;
    let now = new Date(0);
    this.clock = () => now;
    const out: Decision[] = [];
    try {
      for (const request of requests) {
        const at = request.at ? new Date(request.at) : null;
        if (at !== null && !Number.isNaN(at.getTime())) now = at;
        out.push(...this.admit(request, "final", false, 0, null, false));
      }
    } finally {
      this.clock = original;
    }
    return out;
  }

  snapshot(): Record<string, unknown> {
    return {
      streamId: this.streamId,
      watermark: this.watermark === null ? null : new Date(this.watermark).toISOString(),
      lastDecision: this.lastDecision === null ? null : this.lastDecision.toISOString(),
      lastSignature: this.lastSignature ?? [],
      lastSignatureAt: this.lastSignatureAt === null ? null : this.lastSignatureAt.toISOString(),
      windowStart: this.windowStart === null ? null : this.windowStart.toISOString(),
      windowCount: this.windowCount,
      stats: this.statsValue.snapshot(),
      pending: this.items.map((item) => ({ ...item })),
      traces: [...this.traces.values()],
    };
  }

  restore(snapshot: Record<string, unknown>): void {
    if (this.closedFlag) throw new Error("stream session is closed");
    this.streamIdValue = typeof snapshot.streamId === "string" ? snapshot.streamId : this.streamId;
    this.watermark = typeof snapshot.watermark === "string" ? Date.parse(snapshot.watermark) : null;
    this.lastDecision =
      typeof snapshot.lastDecision === "string" ? new Date(snapshot.lastDecision) : null;
    const signature = Array.isArray(snapshot.lastSignature) ? snapshot.lastSignature : [];
    this.lastSignature = signature.map((item) => {
      const pair = item as [string, string | null];
      return [String(pair[0]), pair[1] ?? null];
    });
    this.lastSignatureAt =
      typeof snapshot.lastSignatureAt === "string" ? new Date(snapshot.lastSignatureAt) : null;
    this.windowStart = typeof snapshot.windowStart === "string" ? new Date(snapshot.windowStart) : null;
    this.windowCount = Number(snapshot.windowCount ?? 0);
    const stats = snapshot.stats;
    if (stats && typeof stats === "object") {
      Object.assign(this.statsValue, stats);
    }
    const pending = Array.isArray(snapshot.pending) ? (snapshot.pending as Decision[]) : [];
    this.items.length = 0;
    this.items.push(...pending.slice(-this.capacity));
    if (this.items.length) {
      this.wake();
      if (this.items.length < this.capacity) this.wakeSpace();
    }
    const traces = Array.isArray(snapshot.traces) ? (snapshot.traces as Trace[]) : [];
    for (const trace of traces) {
      this.traces.set(trace.id, trace);
      this.traceByDecision.set(trace.decisionId, trace.id);
    }
  }

  async *decisions(): AsyncIterableIterator<Decision> {
    while (true) {
      if (this.items.length) {
        const decision = this.items.shift()!;
        this.wakeSpace();
        yield decision;
        continue;
      }
      if (this.closedFlag) return;
      await new Promise<void>((resolve) => this.waiters.push(resolve));
    }
  }

  async *feed(
    events: AsyncIterable<DecisionRequest>,
    options: { coalesceMs?: number } = {},
  ): AsyncIterableIterator<Decision> {
    const coalesceMs = options.coalesceMs ?? 0;
    if (coalesceMs <= 0) {
      for await (const event of events) {
        yield* this.admit(event, "final", false, 0, null);
      }
      return;
    }

    const queue: Array<DecisionRequest | null> = [];
    let wake: (() => void) | null = null;
    let done = false;
    const push = (item: DecisionRequest | null): void => {
      queue.push(item);
      if (wake) {
        const resolve = wake;
        wake = null;
        resolve();
      }
    };
    const pump = (async () => {
      try {
        for await (const event of events) push(event);
      } finally {
        done = true;
        push(null);
      }
    })();

    let pending: DecisionRequest | null = null;
    try {
      while (true) {
        if (!queue.length) {
          if (done) break;
          await new Promise<void>((resolve) => {
            wake = resolve;
          });
          continue;
        }

        while (queue.length) {
          const item = queue.shift()!;
          if (item === null) {
            done = true;
            break;
          }
          pending = item;
        }
        if (done) {
          if (pending) yield* this.admit(pending, "final", false, 0, null);
          break;
        }

        const result = await Promise.race<"timeout" | "item">([
          new Promise<"timeout">((resolve) => setTimeout(() => resolve("timeout"), coalesceMs)),
          new Promise<"item">((resolve) => {
            wake = () => resolve("item");
          }),
        ]);
        if (result === "timeout") {
          if (pending) {
            yield* this.admit(pending, "final", false, 0, null);
            pending = null;
          }
        }
      }
    } finally {
      await pump.catch(() => undefined);
    }
  }

  close(): void {
    this.closedFlag = true;
    this.wake();
    this.wakeSpace();
  }

  private admit(
    request: DecisionRequest,
    status: DecisionStatus,
    force: boolean,
    revision: number,
    supersedes: string | null,
    record = true,
  ): Decision[] {
    if (this.closedFlag) throw new Error("stream session is closed");
    if (!DECISION_STATUSES.includes(status)) throw new Error(`unknown decision status: ${status}`);

    this.statsValue.observed += 1;
    const now = this.clock();

    if (this.dedupeMs > 0 && request.eventId) {
      this.purgeSeen(now);
      if (this.seen.has(request.eventId)) {
        this.statsValue.duplicates += 1;
        return [];
      }
      this.seen.set(request.eventId, now.getTime());
    }

    const eventAt = request.at ? Date.parse(request.at) : Number.NaN;
    if (!Number.isNaN(eventAt)) {
      if (this.watermark !== null && eventAt < this.watermark) {
        if (this.late === "drop") {
          this.statsValue.late += 1;
          return [];
        }
      } else {
        this.watermark = eventAt;
      }
    }

    if (!force && this.cooldownMs > 0 && this.lastDecision !== null) {
      const elapsed = now.getTime() - this.lastDecision.getTime();
      if (elapsed < this.cooldownMs) {
        this.statsValue.throttled += 1;
        return [];
      }
    }

    if (!force && !this.allowBudget(now)) {
      return [];
    }

    const deadlineAt = request.deadline ? Date.parse(request.deadline) : Number.NaN;
    const expired = !Number.isNaN(deadlineAt) && now.getTime() > deadlineAt;
    const effectiveStatus: DecisionStatus = expired && status === "final" ? "provisional" : status;

    const started = performance.now();
    const raw = this.decide(request) ?? [];
    this.recordLatency(performance.now() - started);
    const decisions = raw.map((item) => this.stamp(item, request, effectiveStatus, revision, supersedes));
    if (!decisions.length) return [];

    const signature = decisions.map((item) => [item.verb, item.actionId ?? null] as [string, string | null]);
    if (!force && this.hysteresisMs > 0 && this.lastSignature !== null && this.lastSignatureAt !== null) {
      const same =
        signature.length === this.lastSignature.length &&
        signature.every(
          (item, index) =>
            item[0] === this.lastSignature![index]![0] && item[1] === this.lastSignature![index]![1],
        );
      const within = now.getTime() - this.lastSignatureAt.getTime() < this.hysteresisMs;
      if (same && within) {
        this.statsValue.suppressed += decisions.length;
        this.lastDecision = now;
        return [];
      }
    }

    this.lastSignature = signature;
    this.lastSignatureAt = now;
    this.statsValue.decided += decisions.length;
    if (effectiveStatus === "provisional") this.statsValue.provisional += decisions.length;
    if (expired) this.statsValue.expired += decisions.length;
    if (revision) this.statsValue.revised += decisions.length;
    this.lastDecision = now;
    if (record) this.recordDecisions(decisions);
    return decisions;
  }

  private purgeSeen(now: Date): void {
    const cutoff = now.getTime() - this.dedupeMs;
    while (this.seen.size) {
      const [eventId, seenAt] = this.seen.entries().next().value as [string, number];
      if (seenAt <= cutoff || this.seen.size > 4096) {
        this.seen.delete(eventId);
      } else {
        return;
      }
    }
  }

  private recordDecisions(decisions: Decision[]): void {
    for (const decision of decisions) {
      if (this.traceEnabled && decision.traceId) {
        const trace: Trace = {
          id: decision.traceId,
          decisionId: decision.decisionId ?? "",
          events: [
            {
              at: new Date().toISOString(),
              stage: "decided",
              detail: {
                verb: decision.verb,
                reasonCode: decision.reasonCode,
                streamId: decision.streamId,
                eventTime: decision.eventTime,
                revision: decision.revision,
                status: decision.status,
              },
            },
          ],
        };
        this.traces.set(decision.traceId, trace);
        this.traceByDecision.set(decision.decisionId ?? "", decision.traceId);
      }
      this.recorder?.(decision);
    }
  }

  private allowBudget(now: Date): boolean {
    if (this.maxDecisions === null) return true;
    if (this.windowStart === null || now.getTime() - this.windowStart.getTime() >= this.budgetWindowMs) {
      this.windowStart = now;
      this.windowCount = 0;
    }
    if (this.windowCount >= this.maxDecisions) {
      this.statsValue.shed += 1;
      return false;
    }
    this.windowCount += 1;
    return true;
  }

  private recordLatency(elapsed: number): void {
    this.latencies.push(elapsed);
    while (this.latencies.length > this.latencySamples) this.latencies.shift();
    const ordered = [...this.latencies].sort((left, right) => left - right);
    this.statsValue.latencyP50 = this.percentile(ordered, 50);
    this.statsValue.latencyP95 = this.percentile(ordered, 95);
    this.statsValue.latencyP99 = this.percentile(ordered, 99);
  }

  private percentile(ordered: number[], percent: number): number {
    if (!ordered.length) return 0;
    const index = Math.round((percent / 100) * (ordered.length - 1));
    return Number(ordered[Math.max(0, Math.min(ordered.length - 1, index))]!.toFixed(3));
  }

  private stamp(
    decision: Decision,
    request: DecisionRequest,
    status: DecisionStatus,
    revision: number,
    supersedes: string | null,
  ): Decision {
    const stamped: Decision = {
      ...decision,
      streamId: this.streamId,
      eventTime: request.at,
      deadline: request.deadline ?? decision.deadline ?? null,
      validUntil: request.validUntil ?? decision.validUntil ?? null,
      supersedes: supersedes ?? decision.supersedes ?? null,
      revision: Math.max(revision, decision.revision ?? 0),
      status,
    };
    return this.traceEnabled && !stamped.traceId ? { ...stamped, traceId: newId("TRC") } : stamped;
  }

  private append(decision: Decision): void {
    if (this.closedFlag) return;
    if (this.items.length < this.capacity) {
      this.items.push(decision);
      this.wake();
      this.wakeSpace();
      return;
    }
    if (this.onFull === "drop_newest") {
      this.statsValue.dropped += 1;
      return;
    }
    if (this.onFull === "drop_oldest") {
      this.items.shift();
      this.statsValue.dropped += 1;
    } else {
      this.statsValue.dropped += this.items.length;
      this.items.length = 0;
    }
    this.items.push(decision);
    this.wake();
    if (this.items.length < this.capacity) this.wakeSpace();
  }

  private wakeSpace(): void {
    const waiters = this.spaceWaiters;
    this.spaceWaiters = [];
    for (const resolve of waiters) resolve();
  }

  private wake(): void {
    const waiters = this.waiters;
    this.waiters = [];
    for (const resolve of waiters) resolve();
  }
}
