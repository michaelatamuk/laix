import {
  commitmentDue,
  commitmentKey,
  commitmentRef,
  commitmentTrusted,
  normalizeCommitment,
  type Commitment,
  type CommitmentRef,
  type NormalizedCommitment,
} from "./commitment.ts";
import { CommitmentLedger } from "./ledger.ts";

export interface CommitmentBlocker {
  ref: CommitmentRef;
  commitment: NormalizedCommitment | null;
  reason: "missing" | "open" | "unverified" | "stale";
}

export interface CommitmentGraphReport {
  missing_refs: CommitmentRef[];
  cycles: CommitmentRef[][];
  stale_refs: CommitmentRef[];
}

export interface BlockerOptions {
  requireVerified?: boolean;
  now?: Date;
  maxVerificationAgeMs?: number;
}

export interface ValidationOptions {
  now?: Date;
  maxVerificationAgeMs?: number;
}

const NEVER = Number.POSITIVE_INFINITY;

function dueAt(commitment: Commitment): number {
  if (!commitment.due) return NEVER;
  const value = Date.parse(commitment.due);
  return Number.isNaN(value) ? NEVER : value;
}

function verifiedAt(commitment: Commitment): number | null {
  if (!commitment.verifiedAt) return null;
  const value = Date.parse(commitment.verifiedAt);
  return Number.isNaN(value) ? null : value;
}

function localRefs(commitment: Commitment): CommitmentRef[] {
  const owner = commitment.owner ?? "local";
  const ledger = commitment.ledger ?? null;
  return (commitment.dependsOn ?? []).map((id) => ({ owner, ledger, id }));
}

export class CommitmentGraph {
  readonly local: CommitmentLedger;
  readonly external: NormalizedCommitment[];
  private readonly items = new Map<string, NormalizedCommitment>();
  private reverse?: Map<string, NormalizedCommitment[]>;
  private criticalPathCache?: NormalizedCommitment[];
  private cyclesCache?: CommitmentRef[][];

  constructor(local: CommitmentLedger | Commitment[], external: Commitment[] = []) {
    this.local = local instanceof CommitmentLedger ? local : new CommitmentLedger(local);
    this.external = external.map((item) => normalizeCommitment(item));
    for (const item of [...this.local.all(), ...this.external]) {
      const key = commitmentKey(commitmentRef(item));
      if (this.items.has(key)) {
        throw new Error(`duplicate commitment ${item.id} for owner ${item.owner}`);
      }
      this.items.set(key, item);
    }
  }

  get commitments(): NormalizedCommitment[] {
    return [...this.items.values()].sort((left, right) =>
      commitmentKey(commitmentRef(left)).localeCompare(commitmentKey(commitmentRef(right))),
    );
  }

  get(ref: CommitmentRef): NormalizedCommitment | null {
    return this.items.get(commitmentKey(ref)) ?? null;
  }

  resolve(ref: CommitmentRef): NormalizedCommitment | null {
    return this.get(ref);
  }

  dependencies(commitment: Commitment): CommitmentRef[] {
    return [...localRefs(commitment), ...(commitment.externalDependsOn ?? [])];
  }

  isFresh(commitment: Commitment, now: Date, maxAgeMs: number): boolean {
    if ((commitment.source ?? "local") !== "verified") return true;
    const verified = verifiedAt(commitment);
    return verified !== null && now.getTime() - verified <= maxAgeMs;
  }

  staleRefs(now: Date, maxAgeMs: number): CommitmentRef[] {
    return uniqueRefs(
      this.commitments
        .filter((item) => !this.isFresh(item, now, maxAgeMs))
        .map((item) => commitmentRef(item)),
    );
  }

  blockers(commitment: Commitment, options: BlockerOptions = {}): CommitmentBlocker[] {
    const found: CommitmentBlocker[] = [];
    const clock = options.maxVerificationAgeMs === undefined ? null : options.now ?? new Date();
    for (const ref of this.dependencies(commitment)) {
      const item = this.get(ref);
      if (!item) {
        found.push({ ref, commitment: null, reason: "missing" });
      } else if (item.status !== "done") {
        found.push({ ref, commitment: item, reason: "open" });
      } else if (options.requireVerified && !commitmentTrusted(item)) {
        found.push({ ref, commitment: item, reason: "unverified" });
      } else if (
        options.requireVerified &&
        options.maxVerificationAgeMs !== undefined &&
        clock !== null &&
        !this.isFresh(item, clock, options.maxVerificationAgeMs)
      ) {
        found.push({ ref, commitment: item, reason: "stale" });
      }
    }
    return found;
  }

  blocked(commitment: Commitment, options: BlockerOptions = {}): boolean {
    return this.blockers(commitment, options).length > 0;
  }

  blockedOpen(options: BlockerOptions = {}): NormalizedCommitment[] {
    return this.local.open().filter((item) => this.blocked(item, options));
  }

  nextActionable(
    now: Date = new Date(),
    options: BlockerOptions = {},
  ): NormalizedCommitment | null {
    const candidates = this.local.open().filter((item) => !this.blocked(item, options));
    if (!candidates.length) return null;
    return [...candidates].sort((left, right) => {
      if (dueAt(left) !== dueAt(right)) return dueAt(left) - dueAt(right);
      if (left.priority !== right.priority) return right.priority - left.priority;
      return left.id < right.id ? -1 : left.id > right.id ? 1 : 0;
    })[0]!;
  }

  missingRefs(commitment?: Commitment): CommitmentRef[] {
    const source = commitment ? [commitment] : this.commitments;
    const found: CommitmentRef[] = [];
    for (const item of source) {
      for (const ref of this.dependencies(item)) {
        if (!this.get(ref)) found.push(ref);
      }
    }
    return uniqueRefs(found);
  }

  unverifiedRefs(): CommitmentRef[] {
    const found: CommitmentRef[] = [];
    for (const item of this.commitments) {
      for (const ref of this.dependencies(item)) {
        const dependency = this.get(ref);
        if (dependency && !commitmentTrusted(dependency)) found.push(ref);
      }
    }
    return uniqueRefs(found);
  }

  validate(options: ValidationOptions = {}): CommitmentGraphReport {
    const stale =
      options.maxVerificationAgeMs === undefined
        ? []
        : this.staleRefs(
            options.now ?? new Date(),
            options.maxVerificationAgeMs,
          );
    return {
      missing_refs: this.missingRefs(),
      cycles: this.cycles(),
      stale_refs: stale,
    };
  }

  ancestors(ref: CommitmentRef): NormalizedCommitment[] {
    const found = new Map<string, NormalizedCommitment>();
    const walk = (current: CommitmentRef, seen: Set<string>): void => {
      const commitment = this.get(current);
      if (!commitment) return;
      for (const dependency of this.dependencies(commitment)) {
        const key = commitmentKey(dependency);
        if (seen.has(key)) continue;
        const item = this.get(dependency);
        if (!item) continue;
        seen.add(key);
        found.set(key, item);
        walk(dependency, seen);
      }
    };
    walk(ref, new Set([commitmentKey(ref)]));
    return sorted(found);
  }

  private reverseIndex(): Map<string, NormalizedCommitment[]> {
    if (!this.reverse) {
      const reverse = new Map<string, NormalizedCommitment[]>();
      for (const item of this.commitments) {
        for (const dependency of this.dependencies(item)) {
          const key = commitmentKey(dependency);
          reverse.set(key, [...(reverse.get(key) ?? []), item]);
        }
      }
      this.reverse = reverse;
    }
    return this.reverse;
  }

  descendants(ref: CommitmentRef): NormalizedCommitment[] {
    const reverse = this.reverseIndex();
    const found = new Map<string, NormalizedCommitment>();
    const walk = (key: string, seen: Set<string>): void => {
      for (const item of reverse.get(key) ?? []) {
        const itemKey = commitmentKey(commitmentRef(item));
        if (seen.has(itemKey)) continue;
        seen.add(itemKey);
        found.set(itemKey, item);
        walk(itemKey, seen);
      }
    };
    walk(commitmentKey(ref), new Set([commitmentKey(ref)]));
    return sorted(found);
  }

  impact(ref: CommitmentRef): NormalizedCommitment[] {
    return this.descendants(ref);
  }

  chain(ref: CommitmentRef): NormalizedCommitment[] {
    const start = this.get(ref);
    if (!start) return [];
    const walk = (item: NormalizedCommitment, seen: Set<string>): NormalizedCommitment[] => {
      let best = [item];
      for (const dependency of this.dependencies(item)) {
        const key = commitmentKey(dependency);
        if (seen.has(key)) continue;
        const child = this.get(dependency);
        if (!child) continue;
        const candidate = [item, ...walk(child, new Set([...seen, key]))];
        if (candidate.length > best.length) best = candidate;
      }
      return best;
    };
    return walk(start, new Set([commitmentKey(ref)]));
  }

  criticalPath(): NormalizedCommitment[] {
    if (!this.criticalPathCache) {
      let best: NormalizedCommitment[] = [];
      for (const item of this.commitments) {
        const path = this.chain(commitmentRef(item));
        if (path.length > best.length) best = path;
      }
      this.criticalPathCache = best;
    }
    return this.criticalPathCache;
  }

  cycles(): CommitmentRef[][] {
    if (this.cyclesCache) return this.cyclesCache;
    const found: CommitmentRef[][] = [];
    const seen = new Set<string>();
    const complete = new Set<string>();

    const walk = (key: string, stack: string[]): void => {
      if (stack.includes(key)) {
        const start = stack.indexOf(key);
        const cycle = [...stack.slice(start), key];
        const canonical = JSON.stringify([...new Set(cycle)].sort());
        if (!seen.has(canonical)) {
          seen.add(canonical);
          found.push(cycle.map((item) => refFromKey(item)));
        }
        return;
      }
      if (complete.has(key)) return;
      const item = this.items.get(key);
      if (!item) return;
      stack.push(key);
      for (const dependency of this.dependencies(item)) {
        walk(commitmentKey(dependency), stack);
      }
      stack.pop();
      complete.add(key);
    };

    for (const key of this.items.keys()) walk(key, []);
    this.cyclesCache = found;
    return found;
  }

  subgraph(refs: CommitmentRef[]): CommitmentGraph {
    const keys = new Set(refs.map((ref) => commitmentKey(ref)));
    return new CommitmentGraph(
      this.local.all().filter((item) => keys.has(commitmentKey(commitmentRef(item)))),
      this.external.filter((item) => keys.has(commitmentKey(commitmentRef(item)))),
    );
  }

  neighborhood(ref: CommitmentRef): CommitmentGraph {
    const found = new Map<string, NormalizedCommitment>();
    const target = this.get(ref);
    if (target) found.set(commitmentKey(ref), target);
    for (const item of [...this.ancestors(ref), ...this.descendants(ref)]) {
      found.set(commitmentKey(commitmentRef(item)), item);
    }
    return this.subgraph([...found.values()].map((item) => commitmentRef(item)));
  }

  redacted(options: { keepSubject?: boolean } = {}): CommitmentGraph {
    const clean = (item: NormalizedCommitment): NormalizedCommitment => ({
      ...item,
      subject: options.keepSubject ? item.subject : "",
      payload: {},
    });
    return new CommitmentGraph(
      this.local.all().map(clean),
      this.external.map(clean),
    );
  }

  toMermaid(): string {
    const ids = new Map<string, string>();
    this.commitments.forEach((item, index) => {
      ids.set(commitmentKey(commitmentRef(item)), `n${index}`);
    });
    const lines = ["flowchart LR"];
    for (const item of this.commitments) {
      const label = `${item.owner} · ${item.id} · ${item.subject} · ${item.status}`
        .replace(/"/g, "'")
        .replace(/\n/g, " ");
      lines.push(`    ${ids.get(commitmentKey(commitmentRef(item)))}["${label}"]`);
    }
    for (const item of this.commitments) {
      for (const [kind, refs] of [
        ["depends_on", localRefs(item)],
        ["external_depends_on", item.externalDependsOn],
      ] as Array<[string, CommitmentRef[]]>) {
        for (const ref of refs) {
          const child = this.get(ref);
          if (!child) continue;
          lines.push(
            `    ${ids.get(commitmentKey(commitmentRef(item)))} -->|${kind}| ${ids.get(commitmentKey(ref))}`,
          );
        }
      }
    }
    return lines.join("\n");
  }

  toDot(): string {
    const ids = new Map<string, string>();
    this.commitments.forEach((item, index) => {
      ids.set(commitmentKey(commitmentRef(item)), `n${index}`);
    });
    const lines = ["digraph commitments {"];
    for (const item of this.commitments) {
      const label = `${item.owner} · ${item.id} · ${item.subject} · ${item.status}`
        .replace(/"/g, '\\"')
        .replace(/\n/g, " ");
      lines.push(`  ${ids.get(commitmentKey(commitmentRef(item)))} [label="${label}"];`);
    }
    for (const item of this.commitments) {
      for (const [kind, refs] of [
        ["depends_on", localRefs(item)],
        ["external_depends_on", item.externalDependsOn],
      ] as Array<[string, CommitmentRef[]]>) {
        for (const ref of refs) {
          const child = this.get(ref);
          if (!child) continue;
          lines.push(
            `  ${ids.get(commitmentKey(commitmentRef(item)))} -> ${ids.get(commitmentKey(ref))} [label="${kind}"];`,
          );
        }
      }
    }
    lines.push("}");
    return lines.join("\n");
  }

  toDict(): Record<string, unknown> {
    return {
      local: this.local.toDict(),
      external: this.external.map((item) => ({
        ...item,
        dependsOn: [...item.dependsOn],
        payload: { ...item.payload },
        externalDependsOn: item.externalDependsOn.map((ref) => ({ ...ref })),
      })),
    };
  }

  static fromDict(payload: {
    local?: { commitments?: Commitment[] };
    external?: Commitment[];
  }): CommitmentGraph {
    return new CommitmentGraph(
      CommitmentLedger.fromDict(payload.local ?? {}),
      payload.external ?? [],
    );
  }
}

function sorted(items: Map<string, NormalizedCommitment>): NormalizedCommitment[] {
  return [...items.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([, item]) => item);
}

function uniqueRefs(refs: CommitmentRef[]): CommitmentRef[] {
  const seen = new Set<string>();
  const result: CommitmentRef[] = [];
  for (const ref of refs) {
    const key = commitmentKey(ref);
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(ref);
  }
  return result;
}

function refFromKey(key: string): CommitmentRef {
  const [owner, ledger, id] = key.split("\u0000");
  return { owner: owner!, ledger: ledger || null, id: id! };
}
