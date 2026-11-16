package dev.laix.decision.signals

import dev.laix.decision.contracts.Intent
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.nio.file.Files
import java.nio.file.Path
import java.time.OffsetDateTime
import kotlin.math.abs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Replays the shared signal-attention contract against this implementation. */
class SignalAttentionConformanceTest {
    private val json = Json
    private val contract: Path = findContract()

    private fun findContract(): Path {
        var dir: Path? = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize()
        while (dir != null) {
            for (candidate in listOf(
                dir.resolve("contracts").resolve("signal-attention.v1.json"),
                dir.resolve("packages").resolve("contracts").resolve("signal-attention.v1.json"),
            )) {
                if (Files.exists(candidate)) return candidate
            }
            dir = dir.parent
        }
        error("could not find signal-attention.v1.json above ${System.getProperty("user.dir")}")
    }

    private fun text(payload: JsonObject, key: String): String? =
        (payload[key] as? JsonPrimitive)?.content?.takeIf { it != "null" }

    private fun bool(payload: JsonObject, key: String, default: Boolean): Boolean =
        (payload[key] as? JsonPrimitive)?.booleanOrNull ?: default

    private fun number(payload: JsonObject, key: String, default: Double): Double =
        (payload[key] as? JsonPrimitive)?.doubleOrNull ?: default

    private fun strings(payload: JsonObject, key: String): List<String> =
        (payload[key] as? JsonArray)?.map { it.jsonPrimitive.content } ?: emptyList()

    private fun intent(value: JsonElement?): Intent? {
        val payload = value as? JsonObject ?: return null
        val capability = payload["capability"]?.jsonPrimitive?.content ?: return null
        val args = (payload["args"] as? JsonObject)?.entries?.associate { (key, item) ->
            key to primitiveValue(item)
        } ?: emptyMap()
        return Intent(capability, args)
    }

    private fun primitiveValue(value: JsonElement): Any? {
        val primitive = value as? JsonPrimitive ?: return value.toString()
        primitive.booleanOrNull?.let { return it }
        primitive.doubleOrNull?.let { return it }
        return primitive.content
    }

    private fun contextFrom(payload: JsonObject): SignalContext {
        val now = OffsetDateTime.parse(
            text(payload, "now") ?: error("a case context needs `now`"),
        )
        val feedback = (payload["feedback"] as? JsonObject)?.entries?.associate { (key, item) ->
            val entry = item.jsonObject
            key to SignalFeedback(
                state = text(entry, "state") ?: "",
                at = text(entry, "at"),
                until = text(entry, "until"),
                note = text(entry, "note"),
            )
        } ?: emptyMap()
        return SignalContext(
            now = now,
            quietHours = QuietHours.parse(text(payload, "quietHours") ?: "22:00-06:00"),
            mode = text(payload, "mode") ?: "shadow",
            stopped = bool(payload, "stopped", false),
            minSeverity = text(payload, "minSeverity") ?: "high",
            minConfidence = number(payload, "minConfidence", 0.0),
            mutedKinds = strings(payload, "mutedKinds"),
            signalInterruptionBudget = (payload["signalInterruptionBudget"] as? JsonPrimitive)?.content?.toIntOrNull(),
            sent = strings(payload, "sent").toSet(),
            feedback = feedback,
            escalateAfterHours = (payload["escalateAfterHours"] as? JsonPrimitive)?.doubleOrNull,
            learned = (payload["learned"] as? JsonObject)?.entries?.associate { (key, item) ->
                key to item.jsonPrimitive.doubleOrNull!!
            } ?: emptyMap(),
            allowAct = bool(payload, "allowAct", false),
        )
    }

    private fun signalFrom(payload: JsonObject): Signal {
        val escalation = payload["escalation"] as? JsonObject
        return Signal(
            id = text(payload, "id") ?: error("a signal needs an id"),
            kind = text(payload, "kind") ?: "signal",
            title = text(payload, "title") ?: "",
            detail = text(payload, "detail") ?: "",
            severity = text(payload, "severity") ?: "low",
            confidence = number(payload, "confidence", 0.5),
            due = text(payload, "due"),
            evidenceRefs = strings(payload, "evidenceRefs"),
            groupKey = text(payload, "groupKey"),
            interruptionCost = number(payload, "interruptionCost", 0.0),
            requiresApproval = bool(payload, "requiresApproval", false),
            intent = intent(payload["intent"]),
            reversible = bool(payload, "reversible", false),
            handover = escalation?.let {
                Intent(
                    "handover",
                    mapOf(
                        "target" to (text(it, "target") ?: ""),
                        "reason" to (text(it, "reason") ?: ""),
                    ),
                )
            },
        )
    }

    private fun compare(actual: Any?, expected: JsonElement): Boolean =
        when (val primitive = expected as? JsonPrimitive) {
            null -> false
            else -> when {
                primitive.booleanOrNull != null -> actual == primitive.booleanOrNull
                primitive.doubleOrNull != null ->
                    actual is Number && abs(actual.toDouble() - primitive.doubleOrNull!!) < 1e-9
                primitive.content == "null" -> actual == null
                else -> actual?.toString() == primitive.content
            }
        }

    private val fields = listOf(
        "verb",
        "reason_code",
        "deliver",
        "record",
        "requires_approval",
        "score",
        "cost_of_waiting",
        "undo_hint",
        "reversible",
    )

    @Test
    fun `every contract vector passes`() {
        val document = json.parseToJsonElement(Files.readString(contract)).jsonObject
        val cases = document.getValue("cases").jsonArray
        assertTrue(cases.size >= 20, "expected at least 20 vectors, got ${cases.size}")

        val problems = mutableListOf<String>()
        for (case in cases) {
            val payload = case.jsonObject
            val id = text(payload, "id") ?: "?"
            val context = contextFrom(payload.getValue("context").jsonObject)
            val signals = payload.getValue("signals").jsonArray.map { signalFrom(it.jsonObject) }
            val expected = payload.getValue("expected").jsonArray
            val actual = decideSignalAttention(signals, context).map { it.asDict() }

            if (expected.size != actual.size) {
                problems += "$id: expected ${expected.size} decisions, got ${actual.size}"
                continue
            }
            for ((want, got) in expected.zip(actual)) {
                val expectedObject = want.jsonObject
                for (field in fields) {
                    if (!expectedObject.containsKey(field)) continue
                    val wantValue = expectedObject.getValue(field)
                    if (!compare(got[field], wantValue)) {
                        problems += "$id: $field expected $wantValue, got ${got[field]}"
                    }
                }
            }
        }

        assertEquals(emptyList(), problems)
    }

    @Test
    fun `quiet hours are inclusive`() {
        val now = OffsetDateTime.parse("2026-11-01T10:00:00+02:00")
        assertTrue(isQuiet(now.withHour(22).withMinute(0), QuietHours("22:00", "06:00")))
        assertTrue(isQuiet(now.withHour(6).withMinute(0), QuietHours("22:00", "06:00")))
        assertTrue(!isQuiet(now.withHour(21).withMinute(59), QuietHours("22:00", "06:00")))
        assertTrue(!isQuiet(now.withHour(6).withMinute(1), QuietHours("22:00", "06:00")))
        assertTrue(!isQuiet(now.withHour(23), "not-a-window"))
    }

    @Test
    fun `dedupe key is signal and day`() {
        val signal = Signal(id = "D-123", kind = "k")
        val now = OffsetDateTime.parse("2026-11-01T23:59:00+02:00")

        assertEquals("D-123:2026-11-01", dedupeKey(signal, now))
    }

    @Test
    fun `rollup orders by severity then due`() {
        val signals = listOf(
            Signal(id = "low", kind = "k", severity = "low", due = "2026-11-02"),
            Signal(id = "critical-late", kind = "k", severity = "critical", due = "2026-11-09"),
            Signal(id = "critical-soon", kind = "k", severity = "critical", due = "2026-11-03"),
        )

        assertEquals(
            listOf("critical-soon", "critical-late", "low"),
            rollup(signals).map { it.id },
        )
    }

    @Test
    fun `trace ids are stable and prefixed`() {
        val signal = Signal(id = "s-1", kind = "k", severity = "high", confidence = 0.9)
        val context = SignalContext(
            now = OffsetDateTime.parse("2026-11-01T10:00:00+02:00"),
            quietHours = null,
        )

        val first = decideSignalAttention(listOf(signal), context).single()
        val second = decideSignalAttention(listOf(signal), context).single()

        assertEquals(first.traceId, second.traceId)
        assertEquals(15, first.traceId.length)
        assertTrue(first.traceId.startsWith("tr-"))
    }

    @Test
    fun `cost of waiting scales with deadline and severity`() {
        val at = OffsetDateTime.parse("2026-11-01T10:00:00+02:00")
        val context = SignalContext(now = at, quietHours = null)
        val due = "2026-11-02T09:00:00+02:00"

        assertEquals(40.0, costOfWaiting(Signal("a", "k", severity = "critical", due = due), context))
        assertEquals(30.0, costOfWaiting(Signal("b", "k", severity = "high", due = due), context))
        assertEquals(
            0.0,
            costOfWaiting(Signal("c", "k", severity = "critical", due = "2026-12-01T09:00:00+02:00"), context),
        )
        assertEquals(0.0, costOfWaiting(Signal("d", "k", severity = "critical"), context))
    }
}
