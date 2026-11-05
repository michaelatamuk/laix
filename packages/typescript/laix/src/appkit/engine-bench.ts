import type { DecisionEngine, DecisionProblem, Plan } from "../core/contract/engine.ts";
import { MDPEngine, MdpModel } from "../core/planners/mdp/mdp.ts";
import { Simulator, compareEngines, type SimulationReport } from "./simulator.ts";

export class FixedActionEngine implements DecisionEngine {
  readonly action: string;

  constructor(action: string) {
    this.action = action;
  }

  solve(_problem: DecisionProblem): Plan {
    return {
      verb: "act",
      confidence: 1,
      reasonCode: "fixed_action",
      rationale: `always choose ${this.action}`,
      actionId: this.action,
    };
  }
}

function chainModel(horizon = 4): MdpModel {
  const states = Array.from({ length: horizon + 1 }, (_, index) => `s${index}`);
  const transitions = Array.from({ length: horizon }, (_, index) => [
    {
      state: `s${index}`,
      action: "go",
      nextState: `s${index + 1}`,
      probability: 1,
      reward: 1,
    },
    {
      state: `s${index}`,
      action: "stay",
      nextState: `s${index}`,
      probability: 1,
      reward: 0,
    },
  ]).flat();
  return new MdpModel({
    states,
    actions: ["go", "stay"],
    transitions,
    start: "s0",
    discount: 0.9,
    horizon,
  });
}

export function runEngineBench(horizon = 4): SimulationReport {
  const model = chainModel(horizon);
  return compareEngines(
    {
      mdp: new MDPEngine(model),
      "stay-baseline": new FixedActionEngine("stay"),
    },
    [
      {
        name: "forward-chain",
        simulator: Simulator.fromMdp(model),
        optimum: horizon,
      },
    ],
  );
}
