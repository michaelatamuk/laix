package dev.laix.decision.contracts

import dev.laix.decision.support.clamp
import dev.laix.decision.support.confidenceBand

/** One cheap or expensive measurement of the subject. */
data class Observation(
    val id: String,
    val at: String,
    val source: String,
    val kind: String,
    val confidence: Double,
    val payload: Map<String, Any?> = emptyMap(),
    val cost: Double = 0.0,
    val latencyMs: Int = 0,
    val schemaVersion: String = SCHEMA_VERSION,
) {
    val normalizedConfidence: Double
        get() = clamp(confidence)

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "at" to at,
            "source" to source,
            "kind" to kind,
            "confidence" to normalizedConfidence,
            "payload" to payload,
            "cost" to cost,
            "latency_ms" to latencyMs,
            "schema_version" to schemaVersion,
        )
}

/** What the experience is trying to improve, with an explicit weight. */
data class Goal(
    val id: String,
    val statement: String,
    val priority: Double = 0.5,
    val metric: String = "",
    val target: Double? = null,
    val deadline: String? = null,
    val schemaVersion: String = SCHEMA_VERSION,
) {
    val normalizedPriority: Double
        get() = clamp(priority)

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "statement" to statement,
            "priority" to normalizedPriority,
            "metric" to metric,
            "target" to target,
            "deadline" to deadline,
            "schema_version" to schemaVersion,
        )
}

/** Clamp a belief confidence into the published bands. */
fun beliefBand(value: Double): String = confidenceBand(value)
