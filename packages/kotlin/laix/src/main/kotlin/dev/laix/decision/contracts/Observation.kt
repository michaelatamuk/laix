package dev.laix.decision.contracts

import dev.laix.decision.support.asNumber
import dev.laix.decision.support.clamp
import dev.laix.decision.support.confidenceBand

/** One cheap or expensive measurement of the subject. */
@ConsistentCopyVisibility
data class Observation private constructor(
    val id: String,
    val at: String,
    val source: String,
    val kind: String,
    val confidence: Double,
    val payload: Map<String, Any?>,
    val cost: Double,
    val latencyMs: Int,
    val schemaVersion: String,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "at" to at,
            "source" to source,
            "kind" to kind,
            "confidence" to confidence,
            "payload" to payload,
            "cost" to cost,
            "latency_ms" to latencyMs,
            "schema_version" to schemaVersion,
        )

    companion object {
        operator fun invoke(
            id: String,
            at: String,
            source: String,
            kind: String,
            confidence: Double,
            payload: Map<String, Any?> = emptyMap(),
            cost: Double = 0.0,
            latencyMs: Int = 0,
            schemaVersion: String = SCHEMA_VERSION,
        ): Observation = create(
            id,
            at,
            source,
            kind,
            clamp(confidence),
            payload,
            cost,
            latencyMs,
            schemaVersion,
        )

        private fun create(
            id: String,
            at: String,
            source: String,
            kind: String,
            confidence: Double,
            payload: Map<String, Any?>,
            cost: Double,
            latencyMs: Int,
            schemaVersion: String,
        ): Observation = Observation(
            id = id,
            at = at,
            source = source,
            kind = kind,
            confidence = confidence,
            payload = payload,
            cost = cost,
            latencyMs = latencyMs,
            schemaVersion = schemaVersion,
        )

        fun fromMap(payload: Map<String, Any?>): Observation =
            invoke(
                id = payload["id"]?.toString() ?: "",
                at = payload["at"]?.toString() ?: "",
                source = payload["source"]?.toString() ?: "",
                kind = payload["kind"]?.toString() ?: "",
                confidence = asNumber(payload["confidence"]) ?: 0.0,
                payload = (payload["payload"] as? Map<*, *>)?.entries?.associate {
                    it.key.toString() to it.value
                } ?: emptyMap(),
                cost = asNumber(payload["cost"]) ?: 0.0,
                latencyMs = asNumber(payload["latency_ms"])?.toInt() ?: 0,
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

/** What the experience is trying to improve, with an explicit weight. */
@ConsistentCopyVisibility
data class Goal private constructor(
    val id: String,
    val statement: String,
    val priority: Double,
    val metric: String,
    val target: Double?,
    val deadline: String?,
    val schemaVersion: String,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "statement" to statement,
            "priority" to priority,
            "metric" to metric,
            "target" to target,
            "deadline" to deadline,
            "schema_version" to schemaVersion,
        )

    companion object {
        operator fun invoke(
            id: String,
            statement: String,
            priority: Double = 0.5,
            metric: String = "",
            target: Double? = null,
            deadline: String? = null,
            schemaVersion: String = SCHEMA_VERSION,
        ): Goal = create(
            id,
            statement,
            clamp(priority),
            metric,
            target,
            deadline,
            schemaVersion,
        )

        private fun create(
            id: String,
            statement: String,
            priority: Double,
            metric: String,
            target: Double?,
            deadline: String?,
            schemaVersion: String,
        ): Goal = Goal(
            id = id,
            statement = statement,
            priority = priority,
            metric = metric,
            target = target,
            deadline = deadline,
            schemaVersion = schemaVersion,
        )

        fun fromMap(payload: Map<String, Any?>): Goal =
            invoke(
                id = payload["id"]?.toString() ?: "",
                statement = payload["statement"]?.toString() ?: "",
                priority = asNumber(payload["priority"]) ?: 0.5,
                metric = payload["metric"]?.toString() ?: "",
                target = asNumber(payload["target"]),
                deadline = payload["deadline"]?.toString(),
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

/** Clamp a belief confidence into the published bands. */
fun beliefBand(value: Double): String = confidenceBand(value)
