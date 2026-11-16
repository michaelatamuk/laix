# laix-decision (Kotlin)

A Kotlin/JVM implementation of the LAIX decision layer. It mirrors the Python and TypeScript
contracts and is intended to share the same JSON fixtures.

## Status

First vertical slice: the core contract and `UtilityPlanner`.

Implemented:

- `Verb`, `Belief`, `Constraint`, `ActionOption`, `Situation`, `Intent`
- `PlannerInput`, `PlannerResult`, `Planner`
- `UtilityWeights`, `UtilityModel`, `UtilityPlanner`
- `UtilityPlanner` tests

Next:

- decision dispatch and `Decision`
- commitment ledger and graph
- remaining planners and policies
- JSON serialization and shared conformance fixtures
- app kit

## Build

```powershell
.\gradlew.bat test
```

Requires Java 17+.
