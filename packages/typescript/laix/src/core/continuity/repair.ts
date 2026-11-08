export type ConflictRule = [
  leftKind: string,
  leftStatus: string,
  rightKind: string,
  rightStatus: string,
];

export const DEFAULT_CONFLICT_RULES: ConflictRule[] = [
  ["approval", "rejected", "receipt", "executed"],
  ["commitment", "cancelled", "commitment", "done"],
  ["decision", "superseded", "decision", "final"],
];

export interface ContinuityRecord {
  id: string;
  kind: string;
  status: string;
  refs?: string[];
  conflicts?: string[];
  supports?: string[];
  cost?: number;
  payload?: Record<string, unknown>;
}

export interface RepairAction {
  recordId: string;
  action: "supersede";
  fromStatus: string;
  toStatus: string;
  cost: number;
  reason: string;
}

export interface RepairPlan {
  conflicts: Array<[string, string]>;
  actions: RepairAction[];
  totalCost: number;
  consistent: boolean;
  method: "greedy" | "exact";
}

function sharedRefs(left: ContinuityRecord, right: ContinuityRecord): boolean {
  const refs = new Set(left.refs ?? []);
  return (right.refs ?? []).some((ref) => refs.has(ref));
}

function matches(
  left: ContinuityRecord,
  right: ContinuityRecord,
  rule: ConflictRule,
): boolean {
  const [leftKind, leftStatus, rightKind, rightStatus] = rule;
  return (
    left.kind === leftKind &&
    left.status === leftStatus &&
    right.kind === rightKind &&
    right.status === rightStatus
  );
}

function conflictPairs(
  records: ContinuityRecord[],
  rules: ConflictRule[],
): Array<[ContinuityRecord, ContinuityRecord]> {
  const byId = new Map(records.map((record) => [record.id, record]));
  const pairs = new Map<string, [ContinuityRecord, ContinuityRecord]>();
  for (const record of records) {
    for (const otherId of record.conflicts ?? []) {
      const other = byId.get(otherId);
      if (!other || other.id === record.id) continue;
      const key = [record.id, other.id].sort().join("|");
      pairs.set(key, [record, other]);
    }
  }
  for (let leftIndex = 0; leftIndex < records.length; leftIndex += 1) {
    const left = records[leftIndex]!;
    for (let rightIndex = leftIndex + 1; rightIndex < records.length; rightIndex += 1) {
      const right = records[rightIndex]!;
      if (!sharedRefs(left, right)) continue;
      if (
        rules.some(
          (rule) => matches(left, right, rule) || matches(right, left, rule),
        )
      ) {
        const key = [left.id, right.id].sort().join("|");
        if (!pairs.has(key)) pairs.set(key, [left, right]);
      }
    }
  }
  return [...pairs.values()];
}

function minimumVertexCover(
  pairs: Array<[ContinuityRecord, ContinuityRecord]>,
): Set<string> {
  if (!pairs.length) return new Set();
  const records = new Map(
    pairs.flatMap(([left, right]) => [left, right]).map((record) => [record.id, record]),
  );
  const edges = pairs.map(
    ([left, right]) => new Set([left.id, right.id]),
  );
  let bestCost = Number.POSITIVE_INFINITY;
  let best: Set<string> = new Set();

  const search = (
    remaining: Array<Set<string>>,
    chosen: Set<string>,
    cost: number,
  ): void => {
    if (!remaining.length) {
      if (cost < bestCost) {
        bestCost = cost;
        best = new Set(chosen);
      }
      return;
    }
    if (cost >= bestCost) return;
    const edge = remaining.reduce((selected, item) => {
      const selectedMin = Math.min(
        ...[...selected].map((node) => records.get(node)?.cost ?? 1),
      );
      const itemMin = Math.min(
        ...[...item].map((node) => records.get(node)?.cost ?? 1),
      );
      return itemMin > selectedMin ? item : selected;
    });
    const order = [...edge].sort((left, right) => {
      const leftCost = records.get(left)?.cost ?? 1;
      const rightCost = records.get(right)?.cost ?? 1;
      return leftCost !== rightCost ? leftCost - rightCost : left < right ? -1 : 1;
    });
    for (const node of order) {
      search(
        remaining.filter((item) => !item.has(node)),
        new Set([...chosen, node]),
        cost + Math.max(0, records.get(node)?.cost ?? 1),
      );
    }
  };

  search(edges, new Set(), 0);
  return best;
}

export function repairContinuity(
  records: ContinuityRecord[],
  rules: ConflictRule[] = DEFAULT_CONFLICT_RULES,
  options: { exact?: boolean } = {},
): RepairPlan {
  const pairs = conflictPairs(records, rules);
  const active = pairs.filter(
    ([left, right]) => left.status !== "superseded" && right.status !== "superseded",
  );
  const exact = options.exact ?? false;
  const actions: RepairAction[] = [];
  if (exact) {
    const selected = minimumVertexCover(active);
    for (const recordId of [...selected].sort()) {
      const record = records.find((item) => item.id === recordId);
      if (!record) continue;
      actions.push({
        recordId: record.id,
        action: "supersede",
        fromStatus: record.status,
        toStatus: "superseded",
        cost: Math.round(Math.max(0, record.cost ?? 1) * 1e6) / 1e6,
        reason: "minimum-weight vertex cover",
      });
    }
  } else {
    for (const [left, right] of active) {
      let target: ContinuityRecord;
      let other: ContinuityRecord;
      const leftCost = left.cost ?? 1;
      const rightCost = right.cost ?? 1;
      if (leftCost < rightCost) {
        target = left;
        other = right;
      } else if (rightCost < leftCost) {
        target = right;
        other = left;
      } else if (left.id > right.id) {
        target = left;
        other = right;
      } else {
        target = right;
        other = left;
      }
      actions.push({
        recordId: target.id,
        action: "supersede",
        fromStatus: target.status,
        toStatus: "superseded",
        cost: Math.round(Math.max(0, target.cost ?? 1) * 1e6) / 1e6,
        reason: `conflicts with ${other.id}`,
      });
    }
  }
  return {
    conflicts: pairs.map(([left, right]) => [left.id, right.id].sort() as [string, string]),
    actions,
    totalCost:
      Math.round(actions.reduce((total, action) => total + action.cost, 0) * 1e6) /
      1e6,
    consistent: active.length === 0,
    method: exact ? "exact" : "greedy",
  };
}
