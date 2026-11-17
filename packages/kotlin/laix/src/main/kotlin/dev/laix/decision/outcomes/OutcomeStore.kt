package dev.laix.decision.outcomes

import dev.laix.decision.support.toJson
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import java.nio.file.AtomicMoveNotSupportedException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption

/** What an app supplies when outcomes outlive one request. */
interface OutcomeStore {
    fun add(outcome: Outcome): Outcome

    fun forDecision(decisionId: String): List<Outcome>

    fun all(): List<Outcome>

    fun summary(): Map<String, Any?>
}

/**
 * An outcome ledger persisted as one JSON file.
 *
 * The store is append-oriented: `add` and `record` write the file after every
 * change. The host can replace the file with its own database port.
 */
class FileOutcomeStore(
    val directory: Path,
    val filename: String = "outcomes.json",
    tolerance: Double = 1e-9,
) : OutcomeLedger(tolerance = tolerance) {
    val path: Path = directory.resolve(filename)

    init {
        Files.createDirectories(directory)
        records += load()
    }

    private fun load(): List<Outcome> {
        if (!Files.exists(path)) return emptyList()
        val document = Json.parseToJsonElement(Files.readString(path)).jsonObject
        val outcomes = document["outcomes"] as? JsonArray ?: return emptyList()
        return outcomes.mapNotNull { item ->
            (item as? JsonObject)?.let {
                Outcome.fromMap(
                    it.entries.associate { entry -> entry.key to anyValue(entry.value) },
                )
            }
        }
    }

    private fun flush() {
        val document = linkedMapOf("outcomes" to records.map { it.toMap() })
        val temporary = path.resolveSibling("${path.fileName}.tmp")
        Files.writeString(temporary, document.toJson(pretty = true), Charsets.UTF_8)
        try {
            Files.move(
                temporary,
                path,
                StandardCopyOption.REPLACE_EXISTING,
                StandardCopyOption.ATOMIC_MOVE,
            )
        } catch (_: AtomicMoveNotSupportedException) {
            Files.move(temporary, path, StandardCopyOption.REPLACE_EXISTING)
        }
    }

    override fun add(outcome: Outcome): Outcome {
        super.add(outcome)
        flush()
        return outcome
    }

    override fun record(
        decisionId: String,
        metric: String,
        before: Double,
        after: Double,
        attributed: Boolean,
        direction: String,
        evidence: Map<String, Any?>,
        note: String,
        label: String?,
        measuredAt: String?,
        tolerance: Double?,
    ): Outcome {
        val outcome = super.record(
            decisionId,
            metric,
            before,
            after,
            attributed,
            direction,
            evidence,
            note,
            label,
            measuredAt,
            tolerance,
        )
        flush()
        return outcome
    }

    private fun anyValue(value: kotlinx.serialization.json.JsonElement): Any? =
        when (value) {
            is JsonObject -> value.entries.associate { it.key to anyValue(it.value) }
            is JsonArray -> value.jsonArray.map { anyValue(it) }
            is JsonPrimitive -> when {
                value.booleanOrNull != null -> value.booleanOrNull
                value.content == "null" -> null
                else -> value.content.toLongOrNull() ?: value.content.toDoubleOrNull() ?: value.content
            }
            else -> null
        }
}
