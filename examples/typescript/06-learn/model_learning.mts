import { ModelLearner } from "../../../packages/typescript/laix/src/index.ts";

const learner = new ModelLearner();
learner.observe("s0", "go", "s1", 2);
learner.observe("s0", "go", "s1", 2);
console.log(
  JSON.stringify(learner.transitionProbabilities("s0", "go")),
  learner.expectedReward("s0", "go"),
);
