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

export function repairContinuity(
  records: ContinuityRecord[],
  rules: ConflictRule[] = DEFAULT_CONFLICT_RULES,
): RepairPlan {
  const pairs = conflictPairs(records, rules);
  const actions: RepairAction[] = [];
  for (const [left, right] of pairs) {
    if (left.status === "superseded" || right.status === "superseded") continue;
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
  return {
    conflicts: pairs.map(([left, right]) => [left.id, right.id].sort() as [string, string]),
    actions,
    totalCost:
      Math.round(actions.reduce((total, action) => total + action.cost, 0) * 1e6) /
      1e6,
    consistent: pairs.length === 0,
  };
}
