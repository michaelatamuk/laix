import type { Decision } from "./contracts.ts";

export interface Case {
  id: string;
  request: unknown;
  expected?: Record<string, unknown>[];
}

export interface Row {
  caseId: string;
  expected: Record<string, unknown>[];
  actual: Record<string, unknown>[];
  mismatches: string[];
  passed: boolean;
}

export interface Report {
  rows: Row[];
  fields: string[];
  total: number;
  passed: number;
  failed: number;
  agreementRate: number;
  toDict(): Record<string, unknown>;
}

function asDict(decision: unknown): Record<string, unknown> {
  if (decision && typeof decision === "object" && "toDict" in decision && typeof (decision as { toDict: unknown }).toDict === "function") {
    return (decision as { toDict: () => Record<string, unknown> }).toDict();
  }
  const item = decision as Record<string, unknown>;
  return {
    verb: item.verb ?? item.action,
    reasonCode: item.reasonCode ?? item.reason,
    deliver: item.deliver ?? true,
    record: item.record ?? true,
    requiresApproval: item.requiresApproval ?? false,
  };
}

export function compare(cases: Case[], decide: (request: unknown) => Array<Decision | Record<string, unknown>>, fields: string[] = ["verb", "reasonCode", "deliver", "record", "requiresApproval"]): Report {
  const rows: Row[] = cases.map((item) => {
    const expected = item.expected ?? [];
    const actual = decide(item.request).map(asDict);
    const mismatches: string[] = [];
    if (actual.length !== expected.length) mismatches.push(`decision count ${actual.length} != ${expected.length}`);
    expected.forEach((want, index) => {
      const got = actual[index] ?? {};
      for (const name of fields) {
        if (name in want && want[name] !== got[name]) mismatches.push(`item ${index}: ${name} ${JSON.stringify(got[name])} != ${JSON.stringify(want[name])}`);
      }
    });
    return { caseId: item.id, expected, actual, mismatches, passed: mismatches.length === 0 };
  });
  const passed = rows.filter((row) => row.passed).length;
  return {
    rows,
    fields,
    total: rows.length,
    passed,
    failed: rows.length - passed,
    agreementRate: rows.length ? Number((passed / rows.length).toFixed(4)) : 1,
    toDict() {
      return {
        cases: rows.length,
        passed,
        failed: rows.length - passed,
        agreementRate: rows.length ? Number((passed / rows.length).toFixed(4)) : 1,
        fields,
        rows: rows.map((row) => ({ case: row.caseId, passed: row.passed, mismatches: row.mismatches, expected: row.expected, actual: row.actual })),
      };
    },
  };
}

export function loadCases(document: { cases?: Record<string, unknown>[] }): Case[] {
  return (document.cases ?? []).map((item) => ({
    id: String(item.id ?? "?"),
    request: item.request,
    expected: (item.expected as Record<string, unknown>[]) ?? [],
  }));
}
