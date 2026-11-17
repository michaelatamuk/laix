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
  negotiation, allocation), rule policies, planning, target/group composition,
  the UCB bandit, simulation and shadow policies
- signal attention: gates, scoring, decisions, outcomes, precision, hazard and
  calibration
- commitments: ledger, stores, graph, resolvers, planner fixtures
- outcomes: ledger, store, calibration, causal attribution, model learning
- app kit: `DecisionClient`, `DecisionRuntime`, execution bridge, async execution
  and sagas, delivery port, experience state and stores, audit records and
  proposals, platform seam, streaming sessions (windows, timeline, sources,
  feed and checkpoints), resource scheduler, live context
- evaluation: parity cases, reports, attention replay and bench, simulation,
  live bench, planner bench and the bench CLI
- JSON: snake_case serialization, file stores, request parsing, CLI,
  OpenTelemetry attribute names, async streaming and JSON-schema validation
- MCP: the stdio server with initialize, ping, tools/list and tools/call

Not ported: Kotlin Multiplatform targets (this package is JVM only), the Python
schema builder, the Python novelty and incident-replay research scripts, and the
Python packaging/publishing setup.

## Conformance

Tests replay the shared contracts in `packages/contracts`:

- `reason-codes.v1.json`
- `signal-attention.v1.json`
- `commitment-graph.v1.json` (graph and planner cases)
- `signal-attention-bench.v1.json`
- `decision.v1.schema.json`

Version checks keep Python, TypeScript and Kotlin on the same version.

## Python parity notes

A few helpers deliberately reproduce Python behaviour that Kotlin does not have
natively:

- `support.round` rounds the exact binary double with banker's rounding, like
  Python's `round`, and keeps a signed zero.
- `support.truthy` is Python `bool()`; `support.policyTruthy` is the token-based
  truthiness the planner policies apply to constraint strings.
- `support.parseIso` normalises to UTC like `parse_iso`; `parseIsoLocal` keeps
  the written offset like `datetime.fromisoformat`.
- `support.iso` renders `timespec="seconds"`; `isoFull` renders `isoformat()`
  with microseconds only when present.
- Decision-record hashes use a canonical JSON writer with `ensure_ascii=True`
  and Python float formatting, so a record sealed in any package verifies in
  the others.
- `Decision` clamps `confidence` on construction and `copy`, like the Python
  record's `__post_init__`.

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

## Bench

```powershell
.\gradlew.bat bench --args="--list"
.\gradlew.bat bench --args="--suite safety --json"
.\gradlew.bat bench --args="--planners"
.\gradlew.bat bench --args="--live"
```

## MCP server

```powershell
.\gradlew.bat mcp
```

The server speaks JSON-RPC over stdio and exposes the `decide` tool for
`policy: auto` and `policy: live`.

## Regenerate the reason-code registry

After editing the shared contract:

```powershell
python scripts/contracts/generate_kotlin_reason_codes.py
```
