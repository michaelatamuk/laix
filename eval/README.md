# Evaluation seed

This folder holds a small set of checks.

| File | What it checks |
|---|---|
| `contracts/attention.v1.json` | 23 timing cases, 24 decisions |
| `contracts/attention-bench.v1.json` | 12 labelled cases for precision, hazard and recall |
| `contracts/decision.v1.schema.json` | the shape of one decision |
| `contracts/decision-record.v1.schema.json` | the shape of one decision record |

Run the checks with the test script in the repository root.

## Next additions

- A held-out set.
- Real user outcomes.
- A causal study.
- Cases for live perception and sub-second timing.

The current files show whether a code change altered behaviour. User studies show how the layer
performs in the world.
