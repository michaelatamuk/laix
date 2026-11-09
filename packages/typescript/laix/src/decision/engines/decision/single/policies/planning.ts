import type { Decision, DecisionRequest } from "../../../../contracts.ts";
import { CommitmentLedger, commitmentDue } from "../../../../domain/commitments/commitments.ts";

export class PlanningPolicy {
  readonly name = "planning.v1";
  readonly ledger: CommitmentLedger;

  constructor(ledger: CommitmentLedger) {
    this.ledger = ledger;
  }

  decide(request: DecisionRequest): Decision[] {
    const parsed = request.at ? new Date(request.at) : new Date();
    const now = Number.isNaN(parsed.getTime()) ? new Date() : parsed;
    const commitment = this.ledger.nextActionable(now);
    if (!commitment) {
      const blocked = this.ledger.next(now);
      if (blocked) {
        return [
          this.decision(
            "ask",
            "blocked_commitment",
            `${blocked.id} waits on another commitment`,
            0.7,
            blocked.id,
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
  ): Decision {
    return {
      verb,
      confidence,
      reasonCode,
      rationale,
      actionId,
      policyVersion: this.name,
    };
  }
}
