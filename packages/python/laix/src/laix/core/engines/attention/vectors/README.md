# LAIX attention contract

These files form part of the one LAIX contract.

| File | Role |
|---|---|
| `attention.v1.json` | the behavioural cases for the attention policy |
| `bench.v1.json` | labelled cases for precision, hazard and recall |

`guide` is the decision verb; `notify` is its delivery form.

The Python policy and the TypeScript policy both read this contract. A change to a gate, a reason
or a score weight is a version change with a new case.
