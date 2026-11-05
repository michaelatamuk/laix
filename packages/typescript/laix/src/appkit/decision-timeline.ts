import type { Decision } from "../core/contracts.ts";
import { TimelineError } from "./timeline-error.ts";

export { TimelineError };

export interface TimelineReport {
  decisions: number;
  chains: number;
  superseded: number;
  valid: boolean;
  issues: string[];
}

type TimelineDecision = Decision & { decisionId: string };

export class DecisionTimeline {
  private readonly byId = new Map<string, TimelineDecision>();
  private readonly order: string[] = [];

  constructor(decisions: Decision[] = []) {
    for (const decision of decisions) this.add(decision);
  }

  add(decision: Decision): Decision {
    const decisionId = decision.decisionId;
    if (!decisionId) throw new TimelineError("decision id is required");
    if (this.byId.has(decisionId)) {
      throw new TimelineError(`duplicate decision id: ${decisionId}`);
    }

    const revision = decision.revision ?? 0;
    const previousId = decision.supersedes ?? null;
    if (revision < 0) throw new TimelineError(`negative revision: ${decisionId}`);
    if (revision === 0 && previousId) {
      throw new TimelineError(
        `root decision ${decisionId} cannot supersede ${previousId}`,
      );
    }
    if (revision > 0) {
      if (!previousId) {
        throw new TimelineError(
          `revision ${revision} of ${decisionId} needs a predecessor`,
        );
      }
      const previous = this.byId.get(previousId);
      if (!previous) {
        throw new TimelineError(
          `unknown predecessor ${previousId} for ${decisionId}`,
        );
      }
      if ((previous.revision ?? 0) + 1 !== revision) {
        throw new TimelineError(
          `revision ${revision} of ${decisionId} must follow ${previous.revision ?? 0}`,
        );
      }
      if (
        previous.streamId &&
        decision.streamId &&
        previous.streamId !== decision.streamId
      ) {
        throw new TimelineError(
          `stream mismatch: ${previous.streamId} -> ${decision.streamId}`,
        );
      }
      if (
        previous.eventTime &&
        decision.eventTime &&
        decision.eventTime < previous.eventTime
      ) {
        throw new TimelineError(
          `event time moved backwards: ${previous.eventTime} -> ${decision.eventTime}`,
        );
      }
    }

    this.byId.set(decisionId, decision as TimelineDecision);
    this.order.push(decisionId);
    return decision;
  }

  get(decisionId: string): TimelineDecision {
    const decision = this.byId.get(decisionId);
    if (!decision) throw new TimelineError(`unknown decision: ${decisionId}`);
    return decision;
  }

  all(): TimelineDecision[] {
    return this.order.map((id) => this.byId.get(id)!);
  }

  history(decisionId: string): TimelineDecision[] {
    const chain: TimelineDecision[] = [];
    const seen = new Set<string>();
    let current: string | null = decisionId;
    while (current) {
      if (seen.has(current)) throw new TimelineError(`cycle at ${current}`);
      seen.add(current);
      const decision = this.get(current);
      chain.push(decision);
      current = decision.supersedes ?? null;
    }
    return chain.reverse();
  }

  supersededIds(): Set<string> {
    const ids = new Set<string>();
    for (const decision of this.byId.values()) {
      if (decision.supersedes) ids.add(decision.supersedes);
    }
    return ids;
  }

  isSuperseded(decisionId: string): boolean {
    return this.supersededIds().has(decisionId);
  }

  current(streamId?: string): TimelineDecision[] {
    const superseded = this.supersededIds();
    return this.all().filter(
      (decision) =>
        !superseded.has(decision.decisionId) &&
        (streamId === undefined || decision.streamId === streamId),
    );
  }

  latest(streamId?: string): TimelineDecision | null {
    for (let index = this.order.length - 1; index >= 0; index -= 1) {
      const decision = this.byId.get(this.order[index]!)!;
      if (streamId === undefined || decision.streamId === streamId) return decision;
    }
    return null;
  }

  late(watermark: string): TimelineDecision[] {
    return this.all().filter(
      (decision) =>
        decision.eventTime !== undefined &&
        decision.eventTime !== null &&
        decision.eventTime < watermark,
    );
  }

  issues(): string[] {
    const issues: string[] = [];
    for (const decision of this.all()) {
      if (!decision.decisionId) {
        issues.push("decision id is required");
        continue;
      }
      const revision = decision.revision ?? 0;
      if (revision === 0) {
        if (decision.supersedes) {
          issues.push(
            `root ${decision.decisionId} supersedes ${decision.supersedes}`,
          );
        }
        continue;
      }
      const previous = decision.supersedes
        ? this.byId.get(decision.supersedes)
        : undefined;
      if (!previous) {
        issues.push(
          `missing predecessor ${decision.supersedes} for ${decision.decisionId}`,
        );
        continue;
      }
      if ((previous.revision ?? 0) + 1 !== revision) {
        issues.push(
          `revision gap ${previous.revision ?? 0} -> ${revision} at ${decision.decisionId}`,
        );
      }
      if (
        previous.streamId &&
        decision.streamId &&
        previous.streamId !== decision.streamId
      ) {
        issues.push(
          `stream mismatch at ${decision.decisionId}: ${previous.streamId} -> ${decision.streamId}`,
        );
      }
      if (
        previous.eventTime &&
        decision.eventTime &&
        decision.eventTime < previous.eventTime
      ) {
        issues.push(`event time backwards at ${decision.decisionId}`);
      }
    }
    return issues;
  }

  assertValid(): void {
    const issues = this.issues();
    if (issues.length) throw new TimelineError(issues.join("; "));
  }

  report(): TimelineReport {
    const superseded = this.supersededIds();
    const issues = this.issues();
    return {
      decisions: this.byId.size,
      chains: this.all().filter(
        (decision) => !superseded.has(decision.decisionId),
      ).length,
      superseded: superseded.size,
      valid: issues.length === 0,
      issues,
    };
  }

  toDict(): { decisions: Decision[] } {
    return { decisions: this.all() };
  }

  static fromDict(payload: { decisions?: Decision[] }): DecisionTimeline {
    return new DecisionTimeline(payload.decisions ?? []);
  }
}
