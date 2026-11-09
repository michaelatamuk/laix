export interface AttentionCandidate {
  id: string;
  risk?: number;
  value?: number;
  commitment?: boolean;
  informationValue?: number;
  waitingCost?: number;
  reviewCost?: number;
  changeProbability?: number;
  deadline?: string | null;
  params?: Record<string, unknown>;
}

export interface AttentionScheduleRow {
  candidateId: string;
  index: number;
  expectedGain: number;
  urgency: number;
  reviewCost: number;
  selected: boolean;
  reason: string;
}

export interface AttentionSchedule {
  now: string;
  budget: number;
  spent: number;
  rows: AttentionScheduleRow[];
  selected: AttentionScheduleRow[];
  deferred: AttentionScheduleRow[];
}

function asDate(value: string | Date | undefined): Date {
  if (value instanceof Date) return value;
  if (typeof value === "string") {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) return parsed;
  }
  return new Date();
}

function round(value: number): number {
  return Math.round(value * 1e6) / 1e6;
}

export class AttentionScheduler {
  readonly name = "aads.v1";
  private readonly riskWeight: number;
  private readonly commitmentWeight: number;
  private readonly informationWeight: number;
  private readonly urgencyHorizonSeconds: number;

  constructor(
    options: {
      riskWeight?: number;
      commitmentWeight?: number;
      informationWeight?: number;
      urgencyHorizonSeconds?: number;
    } = {},
  ) {
    this.riskWeight = options.riskWeight ?? 1;
    this.commitmentWeight = options.commitmentWeight ?? 0.5;
    this.informationWeight = options.informationWeight ?? 0.5;
    this.urgencyHorizonSeconds = Math.max(
      1,
      options.urgencyHorizonSeconds ?? 3600,
    );
  }

  schedule(
    candidates: AttentionCandidate[],
    options: { now?: string | Date; budget?: number } = {},
  ): AttentionSchedule {
    const current = asDate(options.now);
    const limit = Math.max(0, options.budget ?? 1);
    const ordered = candidates.map((candidate) => {
      const reviewCost = Math.max(1e-9, candidate.reviewCost ?? 1);
      const stakes =
        Math.max(0, candidate.value ?? 0) +
        this.riskWeight * Math.max(0, candidate.risk ?? 0) +
        this.commitmentWeight * (candidate.commitment ? 1 : 0) +
        this.informationWeight * Math.max(0, candidate.informationValue ?? 0);
      const expectedGain =
        Math.max(0, candidate.changeProbability ?? 0.5) * stakes;
      const urgency = this.urgency(candidate.deadline, current);
      const index =
        (expectedGain * urgency - Math.max(0, candidate.waitingCost ?? 0)) /
        reviewCost;
      return { candidate, index, expectedGain, urgency, reviewCost };
    });
    ordered.sort((left, right) =>
      right.index !== left.index
        ? right.index - left.index
        : left.candidate.id < right.candidate.id
          ? -1
          : 1,
    );
    let spent = 0;
    const rows: AttentionScheduleRow[] = ordered.map(
      ({ candidate, index, expectedGain, urgency, reviewCost }) => {
        const selected = spent + reviewCost <= limit + 1e-9;
        if (selected) spent += reviewCost;
        return {
          candidateId: candidate.id,
          index: round(index),
          expectedGain: round(expectedGain),
          urgency: round(urgency),
          reviewCost: round(reviewCost),
          selected,
          reason: selected
            ? "within attention budget"
            : "attention budget exhausted",
        };
      },
    );
    return {
      now: current.toISOString(),
      budget: round(limit),
      spent: round(spent),
      rows,
      selected: rows.filter((row) => row.selected),
      deferred: rows.filter((row) => !row.selected),
    };
  }

  private urgency(deadline: string | null | undefined, now: Date): number {
    if (!deadline) return 1;
    const due = asDate(deadline);
    const seconds = (due.getTime() - now.getTime()) / 1000;
    if (seconds <= 0) return 1 + this.urgencyHorizonSeconds;
    return 1 + this.urgencyHorizonSeconds / Math.max(1, seconds);
  }
}
