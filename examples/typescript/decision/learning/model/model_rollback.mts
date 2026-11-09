import { ModelLearner } from "../../../../../packages/typescript/laix/src/index.ts";

const learner = new ModelLearner();
learner.observe("idle", "act", "done", 1.0);
learner.observe("idle", "act", "done", 1.0);

const snapshot = learner.snapshot();
learner.observe("idle", "act", "failed", 0.0);
learner.restore(snapshot);

console.log(learner.transitionProbabilities("idle", "act"));
