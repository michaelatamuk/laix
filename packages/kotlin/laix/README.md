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

Next:

- `decide` dispatch and signal attention
- commitment ledger and graph
- JSON serialization and shared conformance fixtures
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
