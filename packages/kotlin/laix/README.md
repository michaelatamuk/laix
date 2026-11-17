# laix-decision (Kotlin)

A Kotlin/JVM implementation of the LAIX decision layer. It mirrors the Python and
TypeScript packages and uses the shared JSON contracts for conformance.

Start with the [Kotlin guide](../../../docs/01-start/02-first-steps/03-kotlin.md) for install,
the CLI, bench and MCP tasks, and the example suite. The
[example project](../../../examples/kotlin/README.md) has 64 runnable examples.

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

## Known differences from Python

Normal requests and decisions match. These edge cases still differ, and are listed
so a host can judge whether they matter:

- `clamp(NaN)` keeps `NaN`; Python's `min`/`max` yields `1.0`.
- `fromMap` fills a missing required field with its default; Python's `from_dict`
  raises.
- A boolean field given the string `"false"` reads as true and re-serializes as
  `true`; Python keeps the string.
- Nested equality does not coerce numeric types (`[1]` and `[1.0]` differ);
  Python treats them as equal.
- Float rendering of `NaN`/`Infinity` follows JSON (`NaN`, `Infinity`); Python
  `repr` uses `nan`/`inf`.
- File stores write raw UTF-8 JSON; Python's `json.dumps` escapes non-ASCII as
  `\uXXXX`. The parsed data is identical.
- Stream backpressure polls with `delay(1)` instead of waking on an event.
- Retry delays truncate to milliseconds; Python sleeps fractional seconds.
- The MCP supported protocol versions are a hand-maintained list.

## Examples

```powershell
# from the repository root
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="--all"
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin test
```

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
