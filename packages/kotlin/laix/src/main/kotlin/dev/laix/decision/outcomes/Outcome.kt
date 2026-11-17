package dev.laix.decision.outcomes

import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.round
import dev.laix.decision.support.toJson
import dev.laix.decision.support.newId
import dev.laix.decision.support.iso
import dev.laix.decision.contracts.SCHEMA_VERSION

/** The four labels an outcome can carry. */
enum class OutcomeLabel(val value: String) {
    HELPED("helped"),
    NEUTRAL("neutral"),
    HURT("hurt"),
    UNKNOWN("unknown"),
}

val OUTCOME_LABELS: List<String> = OutcomeLabel.entries.map { it.value }
val OUTCOME_DIRECTIONS: List<String> = listOf("higher-better", "lower-better")

/** Whether a decision helped, measured against a named metric. */
data class Outcome(
    val id: String,
    val decisionId: String,
    val metric: String,
    val before: Double,
    val after: Double,
    val delta: Double,
    val label: String,
    val attributed: Boolean = false,
    val direction: String = "higher-better",
    val evidence: Map<String, Any?> = emptyMap(),
    val measuredAt: String = iso(),
    val note: String = "",
    val schemaVersion: String = SCHEMA_VERSION,
) {
    init {
        require(label in OUTCOME_LABELS) { "unknown outcome label: $label" }
        require(direction in OUTCOME_DIRECTIONS) { "unknown outcome direction: $direction" }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "decision_id" to decisionId,
            "metric" to metric,
            "before" to before,
            "after" to after,
            "delta" to delta,
            "label" to label,
            "attributed" to attributed,
            "direction" to direction,
            "evidence" to evidence,
            "measured_at" to measuredAt,
            "note" to note,
            "schema_version" to schemaVersion,
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromJson(text: String): Outcome = fromMap(parseJsonObject(text))

        fun fromMap(payload: Map<String, Any?>): Outcome =
            Outcome(
                id = payload["id"]?.toString()
                    ?: throw IllegalArgumentException("outcome id is required"),
                decisionId = payload["decision_id"]?.toString()
                    ?: throw IllegalArgumentException("decision id is required"),
                metric = payload["metric"]?.toString()
                    ?: throw IllegalArgumentException("metric is required"),
                before = (payload["before"] as? Number)?.toDouble() ?: 0.0,
                after = (payload["after"] as? Number)?.toDouble() ?: 0.0,
                delta = (payload["delta"] as? Number)?.toDouble() ?: 0.0,
                label = payload["label"]?.toString()
                    ?: throw IllegalArgumentException("label is required"),
                attributed = payload["attributed"] as? Boolean ?: false,
                direction = payload["direction"]?.toString() ?: "higher-better",
                evidence = (payload["evidence"] as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: emptyMap(),
                measuredAt = payload["measured_at"]?.toString() ?: iso(),
                note = payload["note"]?.toString() ?: "",
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

private fun signedGain(delta: Double, direction: String): Double =
    if (direction == "higher-better") delta else -delta

private fun labelFor(delta: Double, tolerance: Double, direction: String): String {
    val gain = signedGain(delta, direction)
    return when {
        gain > tolerance -> "helped"
        gain < -tolerance -> "hurt"
        else -> "neutral"
    }
}

/**
 * Outcome learning: did the decision actually help?
 *
 * This records measured outcomes, not clicks. Attribution is explicit:
 * `attributed = true` means the host can defend that the action caused the
 * change; otherwise the label is still recorded but excluded from the
 * attributed summary.
 */
class OutcomeLedger(
    val tolerance: Double = 1e-9,
    val records: MutableList<Outcome> = mutableListOf(),
) {
    fun record(
        decisionId: String,
        metric: String,
        before: Double,
        after: Double,
        attributed: Boolean = false,
        direction: String = "higher-better",
        evidence: Map<String, Any?> = emptyMap(),
        note: String = "",
        label: String? = null,
        measuredAt: String? = null,
        tolerance: Double? = null,
    ): Outcome {
        require(direction in OUTCOME_DIRECTIONS) { "unknown outcome direction: $direction" }
        val delta = round(after - before, 6)
        val resolved = label ?: labelFor(delta, tolerance ?: this.tolerance, direction)
        require(resolved in OUTCOME_LABELS) { "unknown outcome label: $resolved" }
        val outcome = Outcome(
            id = newId("OUT"),
            decisionId = decisionId,
            metric = metric,
            before = before,
            after = after,
            delta = delta,
            label = resolved,
            attributed = attributed,
            direction = direction,
            evidence = evidence,
            measuredAt = measuredAt ?: iso(),
            note = note,
        )
        records += outcome
        return outcome
    }

    fun add(outcome: Outcome): Outcome {
        records += outcome
        return outcome
    }

    fun forDecision(decisionId: String): List<Outcome> =
        records.filter { it.decisionId == decisionId }

    fun all(): List<Outcome> = records.toList()

    /** Measured gain, with attribution coverage stated separately. */
    fun summary(): Map<String, Any?> {
        val attributed = records.filter { it.attributed }
        val improved = attributed.count { it.label == "helped" }
        val hurt = attributed.count { it.label == "hurt" }
        val gains = attributed.map { signedGain(it.delta, it.direction) }
        return linkedMapOf(
            "measured" to records.size,
            "attributed" to attributed.size,
            "attributionCoverage" to round(attributed.size.toDouble() / maxOf(1, records.size), 3),
            "helped" to improved,
            "neutral" to attributed.count { it.label == "neutral" },
            "hurt" to hurt,
            "meanGain" to if (gains.isNotEmpty()) round(gains.sum() / gains.size, 6) else 0.0,
            "precision" to round(improved.toDouble() / maxOf(1, attributed.size), 3),
        )
    }

    fun byMetric(): Map<String, Map<String, Any?>> {
        val rows = linkedMapOf<String, MutableMap<String, Any?>>()
        for (item in records) {
            val bucket = rows.getOrPut(item.metric) {
                linkedMapOf(
                    "measured" to 0,
                    "attributed" to 0,
                    "helped" to 0,
                    "hurt" to 0,
                    "gain" to 0.0,
                )
            }
            bucket["measured"] = (bucket["measured"] as Int) + 1
            if (item.attributed) {
                bucket["attributed"] = (bucket["attributed"] as Int) + 1
                bucket["helped"] = (bucket["helped"] as Int) + if (item.label == "helped") 1 else 0
                bucket["hurt"] = (bucket["hurt"] as Int) + if (item.label == "hurt") 1 else 0
                bucket["gain"] = (bucket["gain"] as Double) + signedGain(item.delta, item.direction)
            }
        }
        for (bucket in rows.values) {
            bucket["gain"] = round(bucket["gain"] as Double, 6)
        }
        return rows
    }

    fun extend(items: Iterable<Outcome>) {
        records += items
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "tolerance" to tolerance,
            "records" to records.map { it.toMap() },
            "summary" to summary(),
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromJson(text: String): OutcomeLedger = fromMap(parseJsonObject(text))

        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): OutcomeLedger =
            OutcomeLedger(
                tolerance = (payload["tolerance"] as? Number)?.toDouble() ?: 1e-9,
                records = (payload["records"] as? List<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { e ->
                        e.key.toString() to e.value
                    }?.let { Outcome.fromMap(it) }
                }?.toMutableList() ?: mutableListOf(),
            )
    }
}
