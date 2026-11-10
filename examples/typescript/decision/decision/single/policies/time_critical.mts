import {
  DecisionClient,
  type Decision,
  type DecisionPolicy,
  type DecisionRequest,
} from "../../../../../../packages/typescript/laix/src/index.ts";

const WINDOW_MINUTES = 6;
const RISK_LIMIT = 0.2;
const WEIGHTS = {
  risk: 0.25,
  delay: 0.05,
  cost: 0.002,
  disruption: 0.15,
  information: 0.2,
};

interface Option {
  id: string;
  verb: "act" | "escalate" | "guide" | "observe" | "wait";
  name: string;
  benefit: number;
  risk: number;
  delayMinutes: number;
  cost: number;
  disruption: number;
  informationGain?: number;
}

const OPTIONS: Option[] = [
  {
    id: "breaker-wet",
    verb: "act",
    name: "cross the wet floor to the breaker",
    benefit: 1,
    risk: 0.9,
    delayMinutes: 0,
    cost: 0,
    disruption: 0,
  },
  {
    id: "breaker-dry",
    verb: "act",
    name: "use the dry corridor to the breaker",
    benefit: 0.85,
    risk: 0.1,
    delayMinutes: 4,
    cost: 0,
    disruption: 0.1,
  },
  {
    id: "electrician",
    verb: "escalate",
    name: "call an electrician",
    benefit: 0.7,
    risk: 0,
    delayMinutes: 15,
    cost: 120,
    disruption: 0.05,
  },
  {
    id: "evacuate",
    verb: "guide",
    name: "keep people out and raise the alarm",
    benefit: 0.6,
    risk: 0.03,
    delayMinutes: 1,
    cost: 0,
    disruption: 0.5,
  },
  {
    id: "look",
    verb: "observe",
    name: "look from the doorway",
    benefit: 0.5,
    risk: 0.05,
    delayMinutes: 2,
    cost: 0,
    disruption: 0,
    informationGain: 1,
  },
  {
    id: "wait",
    verb: "wait",
    name: "wait",
    benefit: 0.1,
    risk: 0,
    delayMinutes: 0,
    cost: 0,
    disruption: 0,
  },
];

class TradeoffPolicy implements DecisionPolicy {
  readonly name = "water-electricity.v2";
  readonly version = "2.0";

  decide(request: DecisionRequest): Decision[] {
    const confidence = Number(request.attributes?.confidence ?? 0.8);
    const applied: string[] = [];
    const eligible: Option[] = [];

    for (const option of OPTIONS) {
      if (option.risk > RISK_LIMIT) {
        applied.push(
          `${option.id} blocked by risk ${option.risk.toFixed(2)} > ${RISK_LIMIT.toFixed(2)}`,
        );
        continue;
      }
      if (option.delayMinutes > WINDOW_MINUTES) {
        applied.push(
          `${option.id} misses the ${WINDOW_MINUTES}-minute window (${option.delayMinutes} min)`,
        );
        continue;
      }
      eligible.push(option);
    }

    const score = (option: Option): number =>
      confidence * option.benefit -
      WEIGHTS.risk * option.risk -
      WEIGHTS.delay * option.delayMinutes -
      WEIGHTS.cost * option.cost -
      WEIGHTS.disruption * option.disruption +
      WEIGHTS.information * (option.informationGain ?? 0) * (1 - confidence);

    const ranked = [...eligible].sort((left, right) => score(right) - score(left));
    const best = ranked[0]!;
    const alternatives = ranked.map((option) => ({
      action_id: option.id,
      score: Math.round(score(option) * 1e4) / 1e4,
      rejected_because:
        option.id === best.id ? "selected" : `outranked by ${best.id}`,
    }));

    return [
      {
        verb: best.verb,
        confidence,
        reasonCode: "tradeoff_score",
        rationale: `${best.name}: benefit ${best.benefit.toFixed(2)} at confidence ${confidence.toFixed(2)}, risk ${best.risk.toFixed(2)}, delay ${best.delayMinutes} min`,
        actionId: best.id,
        score: Math.round(score(best) * 1e4) / 1e4,
        alternatives,
        attributes: { constraints_applied: applied },
        intent:
          best.id !== "electrician"
            ? {
                capability: "handover",
                args: {
                  target: "electrician",
                  reason: "check the socket after the immediate action",
                },
              }
            : null,
      },
    ];
  }
}

function run(confidence: number): void {
  const decision = new DecisionClient({ policy: new TradeoffPolicy() }).decide({
    subject: "water near electricity",
    at: "2026-11-01T10:00:00Z",
    attributes: { confidence },
  })[0]!;
  console.log(
    `confidence ${confidence.toFixed(2)}: ${decision.verb} ${decision.actionId} ${decision.score}`,
  );
  for (const item of decision.alternatives ?? []) {
    console.log(
      " ",
      item.action_id,
      item.score,
      item.rejected_because,
    );
  }
  for (const item of (decision.attributes?.constraints_applied as string[]) ?? []) {
    console.log("  gate", item);
  }
  console.log();
}

run(0.8);
run(0.45);
