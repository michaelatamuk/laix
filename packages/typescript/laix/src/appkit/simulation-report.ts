import type { PlannerScore } from "./simulator.ts";

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class SimulationReport {
  readonly rows: PlannerScore[];

  constructor(rows: PlannerScore[]) {
    this.rows = rows;
  }

  summary(): Record<string, { runs: number; meanReward: number; meanGap: number }> {
    const buckets = new Map<string, PlannerScore[]>();
    for (const row of this.rows) {
      const items = buckets.get(row.planner) ?? [];
      items.push(row);
      buckets.set(row.planner, items);
    }
    return Object.fromEntries(
      [...buckets.entries()]
        .sort(([left], [right]) => (left < right ? -1 : 1))
        .map(([planner, items]) => [
          planner,
          {
            runs: items.length,
            meanReward: round(
              items.reduce((total, item) => total + item.totalReward, 0) / items.length,
            ),
            meanGap: round(
              items.reduce((total, item) => total + (item.optimalityGap ?? 0), 0) /
                items.length,
            ),
          },
        ]),
    );
  }

  best(): string | null {
    const summary = this.summary();
    const planners = Object.keys(summary);
    if (!planners.length) return null;
    return planners.sort((left, right) =>
      summary[right]!.meanReward !== summary[left]!.meanReward
        ? summary[right]!.meanReward - summary[left]!.meanReward
        : left < right
          ? -1
          : 1,
    )[0]!;
  }

  toDict(): Record<string, unknown> {
    return {
      rows: this.rows.map((item) => ({ ...item })),
      summary: this.summary(),
      best: this.best(),
    };
  }
}
