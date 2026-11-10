import type { Decision, DecisionRequest } from "../contracts.ts";
import {
  CommitmentGraph,
  CommitmentLedger,
  commitmentDue,
} from "../domain/commitments/commitments.ts";

export class PlanningPolicy {
  readonly name = "planning.v1";
  readonly ledger: CommitmentLedger;
  readonly commitmentGraph: CommitmentGraph | null;
  readonly requireVerified: boolean;
  readonly maxVerificationAgeMs?: number;

  constructor(
    ledger: CommitmentLedger,
    options: {
      commitmentGraph?: CommitmentGraph;
      requireVerified?: boolean;
      maxVerificationAgeMs?: number;
    } = {},
  ) {
    this.ledger = ledger;
    this.commitmentGraph = options.commitmentGraph ?? null;
    this.requireVerified = options.requireVerified ?? false;
    this.maxVerificationAgeMs = options.maxVerificationAgeMs;
  }

  decide(request: DecisionRequest): Decision[] {
    const parsed = request.at ? new Date(request.at) : new Date();
    const now = Number.isNaN(parsed.getTime()) ? new Date() : parsed;
    const graph = this.commitmentGraph;
    const commitment = graph
      ? graph.nextActionable(now, {
          requireVerified: this.requireVerified,
          maxVerificationAgeMs: this.maxVerificationAgeMs,
        })
      : this.ledger.nextActionable(now);
    const blocked = graph
      ? graph.blockedOpen({
          requireVerified: this.requireVerified,
          now,
          maxVerificationAgeMs: this.maxVerificationAgeMs,
        })
      : this.ledger.blockedOpen();
    if (!commitment) {
      if (blocked.length) {
        const first = blocked[0]!;
        return [
          this.decision(
            "ask",
            "blocked_commitment",
            `${first.id} waits on another commitment`,
            0.7,
            first.id,
            { commitment_id: first.id },
          ),
        ];
      }
      return [this.decision("wait", "no_commitment", "there is no open commitment", 0.8)];
    }
    if (commitmentDue(commitment, now)) {
      return [
        this.decision(
          "act",
          "due_commitment",
          `${commitment.id} is due`,
          0.9,
          commitment.id,
        ),
      ];
    }
    return [
      this.decision(
        "wait",
        "not_due",
        `${commitment.id} is not due yet`,
        0.8,
        commitment.id,
      ),
    ];
  }

  private decision(
    verb: Decision["verb"],
    reasonCode: string,
    rationale: string,
    confidence: number,
    actionId: string | null = null,
    attributes: Record<string, unknown> = {},
  ): Decision {
    return {
      verb,
      confidence,
      reasonCode,
      rationale,
      actionId,
      attributes,
      policyVersion: this.name,
    };
  }
}
