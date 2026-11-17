# Kotlin/JVM

The Kotlin package is the third implementation of the LAIX decision layer, next to Python and
TypeScript. It mirrors the same decision contract, reason codes, planner behaviour and app-kit
surfaces, and it replays the shared JSON contracts in `packages/contracts`.

- Coordinates: `dev.laix:laix-decision:0.18.0` (not published to Maven yet).
- Toolchain: Kotlin 2.1, Gradle 8.12, JDK 17. The Gradle wrapper downloads Gradle and the Kotlin
  toolchain.
- Package root: `packages/kotlin/laix`, source root `src/main/kotlin/dev/laix/decision`.
- It is JVM-only; Kotlin Multiplatform targets are out of scope.

## Install

From a Gradle project, use the checkout as a composite build until the artifact is published:

```kotlin
// settings.gradle.kts
includeBuild("../path/to/laix/packages/kotlin/laix")
```

```kotlin
// build.gradle.kts
dependencies {
    implementation("dev.laix:laix-decision:0.18.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.1")
}
```

`kotlinx-coroutines-core` is only needed for the streaming and async execution surfaces.

## One decision

```kotlin
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb
import dev.laix.decision.decide

val decision = decide(
    DecisionRequest(
        subject = "kitchen sink",
        at = "2026-11-01T10:00:00+00:00",
        situation = Situation(
            id = "sink-1",
            at = "2026-11-01T10:00:00+00:00",
            subject = "kitchen sink",
            beliefs = listOf(
                Belief(
                    id = "overflow",
                    proposition = "the sink is about to overflow",
                    confidence = 0.95,
                ),
            ),
            attributes = mapOf("urgency" to 0.9),
        ),
        options = listOf(
            ActionOption("option-wait", Verb.WAIT, "keep watching", expectedBenefit = 0.1),
            ActionOption(
                "option-close-valve",
                Verb.ACT,
                "close the valve",
                expectedBenefit = 0.95,
                risk = 0.05,
                reversible = true,
            ),
        ),
    ),
).single()

println("${decision.verb.value} ${decision.reasonCode} ${decision.actionId}")
// act policy_rule option-close-valve
```

`decide` selects the action policy or signal attention from the request shape, exactly like the
Python and TypeScript entry points.

## App kit

`DecisionClient` adds execution, records, delivery and streaming around the same decision shape:

```kotlin
import dev.laix.decision.appkit.DecisionClient
import dev.laix.decision.contracts.DecisionRequest

val client = DecisionClient()
val decisions = client.decide(
    DecisionRequest(
        subject = "kitchen sink",
        at = "2026-11-01T10:00:00+00:00",
        situation = situation,
        options = options,
    ),
)
println(client.status())
```

The rest of the app kit maps one-to-one:

| Need | Kotlin |
|---|---|
| runtime facade | `DecisionRuntime` |
| write boundary with approval and receipts | `ExecutionBridge`, `ExecutionStep`, `runSteps` |
| async execution and sagas | `executeAsync`, `runStepsAsync` |
| audit record and proposal | `createRecord`, `approve`, `markExecuted`, `undo`, `verify`, `Proposal` |
| streams and checkpoints | `StreamSession`, `TumblingWindow`, `FileStreamCheckpointStore` |
| state and outcome stores | `ExperienceState`, `FileStateStore`, `FileOutcomeStore` |
| platform seam and delivery | `InMemoryPlatform`, `DeliveryPort`, `NullDelivery` |

## CLI, bench and MCP

From `packages/kotlin/laix`:

```powershell
.\gradlew.bat run --args="explain path\to\decision.json"
.\gradlew.bat run --args="lint path\to\decision.json"
.\gradlew.bat bench --args="--list"
.\gradlew.bat bench --args="--suite safety --json"
.\gradlew.bat bench --args="--planners"
.\gradlew.bat bench --args="--live"
.\gradlew.bat mcp
```

`mcp` runs the same stdio `decide` tool as `laix-mcp`: `initialize`, `ping`, `tools/list` and
`tools/call`, with `policy: auto` and `policy: live`.

## Examples

The Kotlin examples live in `examples/kotlin` and are a Gradle project of their own. They are
executed by CI and by a test that runs every example.

```powershell
# from the repository root
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="--list"
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="--all"
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin run --args="decision/single/planners"
.\packages\kotlin\laix\gradlew.bat -p examples\kotlin test
```

The suite covers decide, every planner family, the packaged policies, sequence, fleet, explain,
domain, learning, evaluation, perception and the app kit. Each example prints one line, so the
output doubles as a conformance sketch. See
[`examples/kotlin/README.md`](../../../examples/kotlin/README.md).

## Conformance and tests

```powershell
cd packages/kotlin/laix
.\gradlew.bat test
.\gradlew.bat build
```

- 355 unit tests, replaying `reason-codes.v1.json`, `signal-attention.v1.json`,
  `commitment-graph.v1.json`, `signal-attention-bench.v1.json` and `decision.v1.schema.json`.
- `scripts/ci/check_versions.py` keeps the Kotlin package version equal to the Python package.
- `scripts/contracts/generate_kotlin_reason_codes.py` regenerates the Kotlin reason-code registry
  from the shared contract.

## Parity notes

A few helpers deliberately reproduce Python semantics:

- `round` rounds the exact binary double with banker's rounding and keeps signed zero.
- `truthy` is Python `bool()`; `policyTruthy` is the token-based truthiness the planner policies
  apply to constraint strings.
- `parseIso` normalises to UTC like `parse_iso`; `parseIsoLocal` keeps the written offset like
  `datetime.fromisoformat`.
- `iso` renders `timespec="seconds"`; `isoFull` renders `isoformat()` with microseconds only when
  present.
- Decision-record hashes use a canonical JSON writer with `ensure_ascii=True` and Python float
  formatting, so a record sealed in any package verifies in the others.

The package README has the full list: [`packages/kotlin/laix/README.md`](../../../packages/kotlin/laix/README.md).

## Limits

- The artifact is not published to Maven Central yet; use the composite build.
- The package is JVM-only.
- The Python schema builder and the Python novelty/incident-replay research scripts are not ported.
- Shared contract vectors cover reason codes, signal attention, commitment graph/planner, the
  attention bench and the decision schema; the other planners are covered by Kotlin unit tests and
  the example suite.
