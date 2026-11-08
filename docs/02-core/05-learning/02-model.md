# Model learning

`ModelLearner` learns a small transition and reward model from observed outcomes. The model is a count
table, not a neural network. It is enough to learn a small domain model from execution outcomes, and it
keeps a best snapshot so a host can reject a learned model that performs worse on a validation set.

```python
from laix import ModelLearner

learner = ModelLearner()
learner.observe(state="idle", action="act", next_state="done", reward=1.0)
model = learner.to_mdp_model()
```

`ModelLearner.rollback()` restores the best snapshot. `LearnedTransition` is the transition record.

## Where it fits

Model learning feeds the MDP planner. It does not change the decision contract; it changes the model a
model-based planner can use.

## Related

- [Model-based planners](../03-decision/01-single/03-model-based.md)
- [Calibration](01-calibration.md)
- [Model learning example](../../../examples/python/core/learning/model/model_learning.py)
