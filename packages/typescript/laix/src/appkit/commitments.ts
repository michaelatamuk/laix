import {
  CommitmentGraph,
  commitmentKey,
  commitmentRef,
  type Commitment,
  type CommitmentLedger,
  type CommitmentRef,
} from "../decision/domain/commitments/commitments.ts";

export interface CommitmentResolver {
  /**
   * Resolve owner-qualified references from host-managed state.
   *
   * The port is synchronous on purpose: LAIX never performs network I/O while
   * planning. A host with a remote source resolves into a local cache first and
   * serves this call from there.
   */
  resolve(refs: CommitmentRef[]): Commitment[];
}

export interface AsyncCommitmentResolver {
  /** An async variant for hosts that fetch before planning. */
  resolve(refs: CommitmentRef[]): Promise<Commitment[]>;
}

export class InMemoryCommitmentResolver implements CommitmentResolver {
  private readonly items = new Map<string, Commitment>();

  constructor(commitments: Commitment[] = []) {
    for (const commitment of commitments) this.add(commitment);
  }

  add(commitment: Commitment): Commitment {
    this.items.set(commitmentKey(commitmentRef(commitment)), commitment);
    return commitment;
  }

  resolve(refs: CommitmentRef[]): Commitment[] {
    const found: Commitment[] = [];
    for (const ref of refs) {
      const item = this.items.get(commitmentKey(ref));
      if (item) found.push(item);
    }
    return found;
  }
}

export function resolveCommitmentGraph(
  local: CommitmentLedger,
  resolver: CommitmentResolver,
): CommitmentGraph {
  return new CommitmentGraph(local, resolver.resolve(externalCommitmentRefs(local)));
}

export async function resolveCommitmentGraphAsync(
  local: CommitmentLedger,
  resolver: AsyncCommitmentResolver,
): Promise<CommitmentGraph> {
  return new CommitmentGraph(
    local,
    await resolver.resolve(externalCommitmentRefs(local)),
  );
}

function externalCommitmentRefs(local: CommitmentLedger): CommitmentRef[] {
  const seen = new Set<string>();
  const refs: CommitmentRef[] = [];
  for (const item of local.all()) {
    for (const ref of item.externalDependsOn) {
      const key = commitmentKey(ref);
      if (seen.has(key)) continue;
      seen.add(key);
      refs.push(ref);
    }
  }
  return refs;
}
