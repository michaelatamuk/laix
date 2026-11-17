# laix-decision (Kotlin)

A Kotlin/JVM implementation of the LAIX decision layer. It mirrors the Python and
TypeScript packages and uses the shared JSON contracts for conformance.

## Status

Implemented:

- contract records: verbs, beliefs, constraints, options, situations, goals,
  observations, requests, decisions, evidence, score breakdowns, reason codes
- planners: utility, commitment (with belief and resolution), execution risk,
  human attention, risk bounded, goal conflict, case based, portfolio, MDP,
  POMDP, CA-VOD, live composite, CABB/rollout/replan
- policies: the action policy and the reference packs (safety, verification,
  preference elicitation, active perception, replanning, escalation,
  negotiation, allocation), rule policies, planning, target/group composition
  and the UCB bandit
- signal attention: gates, scoring, decisions, outcomes, precision, hazard and
  calibration
- commitments: ledger, stores, graph, resolvers, planner fixtures
- outcomes: ledger, store, calibration, causal attribution, model learning
- app kit: `DecisionClient`, `DecisionRuntime`, execution bridge and sagas,
  delivery port, experience state and stores, audit records and proposals,
  platform seam, streaming sessions, resource scheduler, live context
- evaluation: parity cases, reports, attention replay and the attention bench
- JSON: snake_case serialization, file stores, request parsing, CLI and
  OpenTelemetry attribute names
- MCP: the `decide` tool payload for auto and live policies

Not yet ported: the simulation and bench runners, the async execution mixin, the
streaming feed/source/window/timeline extras, JSON-schema validation, the MCP
stdio transport and Kotlin Multiplatform targets.

## Conformance

Tests replay the shared contracts in `packages/contracts`:

- `reason-codes.v1.json`
- `signal-attention.v1.json`
- `commitment-graph.v1.json` (graph and planner cases)
- `signal-attention-bench.v1.json`

Version checks keep Python, TypeScript and Kotlin on the same version.

## Build

```powershell
.\gradlew.bat test
```

Requires Java 17+.

## CLI

```powershell
.\gradlew.bat run --args="explain path\to\decision.json"
.\gradlew.bat run --args="explain path\to\decision.json --json"
.\gradlew.bat run --args="lint path\to\decision.json"
```

## Regenerate the reason-code registry

After editing the shared contract:

```powershell
python scripts/contracts/generate_kotlin_reason_codes.py
```
