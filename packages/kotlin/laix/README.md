# laix-decision (Kotlin)

A Kotlin/JVM implementation of the LAIX decision layer. It mirrors the Python and TypeScript
contracts and is intended to share the same JSON fixtures.

## Status

Second vertical slice: the decision contract on top of the core records.

Implemented:

- `Verb`, `Belief`, `Constraint`, `ActionOption`, `Situation`, `Intent`
- `PlannerInput`, `PlannerResult`, `Planner`
- `UtilityWeights`, `UtilityModel`, `UtilityPlanner`
- `Decision`, `DecisionRequest`, `EvidenceRef`, `ScoreBreakdown`
- `DecisionPolicy`, `PlannerPolicy`, `toPlannerInput`, `toDecision`
- generated `ReasonCodes` registry, checked against `packages/contracts/reason-codes.v1.json`
- `ActionPolicy`, `ActionPolicyConfig`, `ActionPolicyInput`, `decideAction`
- `Signal`, `SignalContext`, `SignalFeedback`, gates and `decideSignalAttention`
- `decide` dispatch with `select`, `attributesFor`, `annotateConfidence`, `coerce`
- conformance against `packages/contracts/signal-attention.v1.json`
- `Commitment`, `CommitmentRef`, `CommitmentLedger`, stores and `CommitmentGraph`
- `CommitmentPlanner` with effect, weights and rejection codes
- conformance against the graph and planner cases in `packages/contracts/commitment-graph.v1.json`

Next:

- remaining single planners and policies
- JSON serialization and schema checks
- shared conformance fixtures for planner cases
- app kit

## Build

```powershell
.\gradlew.bat test
```

Requires Java 17+.

Regenerate the reason-code registry after editing the shared contract:

```powershell
python scripts/contracts/generate_kotlin_reason_codes.py
```
