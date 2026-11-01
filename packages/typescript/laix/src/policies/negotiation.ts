import type { Decision, DecisionRequest } from "../contracts.ts";
import { makeDecision, numberValue } from "./support.ts";

export class NegotiationPolicy {
  name = "negotiation.v1";
  version = "0.6.1";

  decide(request: DecisionRequest): Decision[] {
    const offer = numberValue(request, "offer", 0);
    const reservation = numberValue(request, "reservation", 0);
    const target = numberValue(request, "target", reservation);
    const round = Math.trunc(numberValue(request, "round", 1));
    const maxRounds = Math.trunc(numberValue(request, "max_rounds", 5));

    if (offer >= reservation) {
      return [makeDecision({ policy: this.name, verb: "act", reasonCode: "accept_offer", rationale: `the offer ${offer.toFixed(2)} meets the reservation ${reservation.toFixed(2)}`, confidence: 0.95, intent: { capability: "accept_offer", args: { amount: offer } }, actionId: "accept_offer" })];
    }
    if (round >= maxRounds) {
      return [makeDecision({ policy: this.name, verb: "escalate", reasonCode: "round_limit", rationale: "the round limit is reached without an acceptable offer", confidence: 0.8 })];
    }
    const counter = Math.max(reservation, (offer + target) / 2);
    return [makeDecision({ policy: this.name, verb: "act", reasonCode: "counter_offer", rationale: `counter at ${counter.toFixed(2)}, between the offer ${offer.toFixed(2)} and target ${target.toFixed(2)}`, confidence: 0.7, intent: { capability: "counter_offer", args: { amount: counter } }, actionId: "counter_offer" })];
  }
}
