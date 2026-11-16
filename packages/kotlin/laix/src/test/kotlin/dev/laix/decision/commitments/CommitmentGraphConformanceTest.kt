package dev.laix.decision.commitments

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals

class CommitmentGraphConformanceTest {
    private val contract: Path = findContract()

    private fun findContract(): Path {
        var dir: Path? = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize()
        while (dir != null) {
            for (candidate in listOf(
                dir.resolve("contracts").resolve("commitment-graph.v1.json"),
                dir.resolve("packages").resolve("contracts").resolve("commitment-graph.v1.json"),
            )) {
                if (Files.exists(candidate)) return candidate
            }
            dir = dir.parent
        }
        error("could not find commitment-graph.v1.json above ${System.getProperty("user.dir")}")
    }

    private fun JsonElement.anyMap(): Map<String, Any?> =
        jsonObject.entries.associate { (key, value) -> key to anyValue(value) }

    private fun anyValue(value: JsonElement): Any? =
        when (value) {
            is JsonObject -> value.anyMap()
            is JsonArray -> value.map { anyValue(it) }
            is JsonPrimitive -> when {
                value.booleanOrNull != null -> value.booleanOrNull
                value.content == "null" -> null
                value.content.toDoubleOrNull() != null -> value.content.toDouble()
                else -> value.content
            }
            else -> null
        }

    private fun commitment(value: JsonObject): Commitment =
        Commitment.fromMap(value.anyMap())

    private fun ref(value: Map<String, Any?>): Map<String, Any?> =
        linkedMapOf(
            "owner" to value["owner"],
            "ledger" to value["ledger"],
            "id" to value["id"],
        )

    @Test
    fun `every graph fixture case passes`() {
        val payload = Json.parseToJsonElement(Files.readString(contract)).jsonObject
        val cases = payload.getValue("cases").jsonArray

        for (case in cases) {
            val fields = case.jsonObject
            val id = fields.getValue("id").jsonPrimitive.content
            val local = CommitmentLedger(
                fields.getValue("local").jsonArray.map { commitment(it.jsonObject) },
            )
            val external = fields.getValue("external").jsonArray.map { commitment(it.jsonObject) }
            val graph = CommitmentGraph(local, external)
            val expected = fields.getValue("expected").jsonObject
            val target = local.get(fields.getValue("target").jsonPrimitive.content)

            assertEquals(
                expected.getValue("blocked").jsonPrimitive.booleanOrNull,
                graph.blocked(target),
                "$id blocked",
            )
            assertEquals(
                expected.getValue("blocked_verified").jsonPrimitive.booleanOrNull,
                graph.blocked(target, requireVerified = true),
                "$id blocked_verified",
            )
            assertEquals(
                expected.getValue("blockers").jsonArray.map { (it as JsonObject).anyMap() },
                graph.blockers(target, requireVerified = true).map { it.toMap() },
                "$id blockers",
            )
            assertEquals(
                expected.getValue("missing_refs").jsonArray.map { ref((it as JsonObject).anyMap()) },
                graph.missingRefs().map { ref(it.toMap()) },
                "$id missing_refs",
            )
            assertEquals(
                expected.getValue("unverified_refs").jsonArray.map { ref((it as JsonObject).anyMap()) },
                graph.unverifiedRefs().map { ref(it.toMap()) },
                "$id unverified_refs",
            )

            if (expected.containsKey("chain")) {
                val chainRef = CommitmentRef(
                    owner = "local",
                    ledger = null,
                    id = fields.getValue("chain_from").jsonPrimitive.content,
                )
                assertEquals(
                    expected.getValue("chain").jsonArray.map { it.jsonPrimitive.content },
                    graph.chain(chainRef).map { it.id },
                    "$id chain",
                )
            }
            if (expected.containsKey("impact")) {
                val impactRef = CommitmentRef(
                    owner = "local",
                    ledger = null,
                    id = fields.getValue("impact_from").jsonPrimitive.content,
                )
                assertEquals(
                    expected.getValue("impact").jsonArray.map { it.jsonPrimitive.content },
                    graph.impact(impactRef).map { it.id },
                    "$id impact",
                )
            }
            if (expected.containsKey("critical_path")) {
                assertEquals(
                    expected.getValue("critical_path").jsonArray.map { it.jsonPrimitive.content },
                    graph.criticalPath().map { it.id },
                    "$id critical_path",
                )
            }
            if (expected.containsKey("cycles")) {
                val actual = graph.cycles().map { cycle -> cycle.map { it.id }.toSet() }.toSet()
                val wanted = expected.getValue("cycles").jsonArray.map { cycle ->
                    cycle.jsonArray.map { it.jsonPrimitive.content }.toSet()
                }.toSet()
                assertEquals(wanted, actual, "$id cycles")
            }
        }
    }

    @Test
    fun `a graph round-trips through maps`() {
        val graph = CommitmentGraph(
            CommitmentLedger(listOf(Commitment(id = "a", subject = "a"))),
            listOf(
                Commitment(
                    id = "b",
                    subject = "b",
                    owner = "other",
                    ledger = "other",
                    source = "reported",
                ),
            ),
        )

        val restored = CommitmentGraph.fromMap(graph.toMap())

        assertEquals(graph.toMap(), restored.toMap())
        assertEquals(listOf("a", "b"), restored.commitments.map { it.id })
    }

    @Test
    fun `the ledger ranks by due then priority`() {
        val ledger = CommitmentLedger(
            listOf(
                Commitment(id = "later", subject = "later", due = "2026-11-02T10:00:00+00:00"),
                Commitment(id = "sooner", subject = "sooner", due = "2026-11-01T10:00:00+00:00"),
                Commitment(id = "priority", subject = "priority", priority = 0.9),
                Commitment(id = "urgent", subject = "urgent", due = "2026-11-01T10:00:00+00:00", priority = 0.9),
            ),
        )

        assertEquals("urgent", ledger.next()?.id)
        assertEquals("urgent", ledger.nextActionable()?.id)
    }

    @Test
    fun `renderers keep one node per commitment`() {
        val graph = CommitmentGraph(
            CommitmentLedger(
                listOf(Commitment(id = "a", subject = "first"), Commitment(id = "b", subject = "second", dependsOn = listOf("a"))),
            ),
        )

        assertEquals(4, graph.toMermaid().lines().size)
        assertEquals(5, graph.toDot().lines().size)
    }
}
