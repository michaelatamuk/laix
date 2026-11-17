package dev.laix.decision.commitments

import dev.laix.decision.support.parseIso
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import java.time.OffsetDateTime

val COMMITMENT_STATUSES: List<String> = listOf("open", "done", "cancelled")
val COMMITMENT_SOURCES: List<String> = listOf("local", "reported", "verified")

/** A qualified reference to one commitment. */
data class CommitmentRef(
    val owner: String,
    val id: String,
    val ledger: String? = null,
) {
    init {
        require(owner.isNotEmpty()) { "commitment owner must not be empty" }
        require(id.isNotEmpty()) { "commitment id must not be empty" }
    }

    /** The stable lookup key used by [CommitmentGraph]. */
    val key: Triple<String, String, String>
        get() = Triple(owner, ledger ?: "", id)

    fun toMap(): Map<String, Any?> =
        linkedMapOf("owner" to owner, "id" to id, "ledger" to ledger)

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromJson(text: String): CommitmentRef = fromMap(parseJsonObject(text))
        fun fromMap(payload: Map<String, Any?>): CommitmentRef =
            CommitmentRef(
                owner = payload["owner"]?.toString()
                    ?: throw IllegalArgumentException("commitment owner is required"),
                id = payload["id"]?.toString()
                    ?: throw IllegalArgumentException("commitment id is required"),
                ledger = payload["ledger"]?.toString(),
            )
    }
}

/** One promised step, with its due time, owner and dependencies. */
data class Commitment(
    val id: String,
    val subject: String,
    val due: String? = null,
    val status: String = "open",
    val dependsOn: List<String> = emptyList(),
    val priority: Double = 0.5,
    val payload: Map<String, Any?> = emptyMap(),
    val owner: String = "local",
    val ledger: String? = null,
    val source: String = "local",
    val verifiedAt: String? = null,
    val externalDependsOn: List<CommitmentRef> = emptyList(),
) {
    init {
        require(status in COMMITMENT_STATUSES) { "unknown commitment status: $status" }
        require(source in COMMITMENT_SOURCES) { "unknown commitment source: $source" }
        require(owner.isNotEmpty()) { "commitment owner must not be empty" }
    }

    /** The stable lookup key used by [CommitmentGraph]. */
    val key: Triple<String, String, String>
        get() = Triple(owner, ledger ?: "", id)

    /** Local and timestamped verified commitments may be decision evidence. */
    val trusted: Boolean
        get() = when (source) {
            "local" -> true
            "verified" -> parseIso(verifiedAt) != null
            else -> false
        }

    fun isDue(now: OffsetDateTime): Boolean {
        val moment = parseIso(due) ?: return false
        return !moment.toInstant().isAfter(now.toInstant())
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "subject" to subject,
            "due" to due,
            "status" to status,
            "depends_on" to dependsOn,
            "priority" to priority,
            "payload" to payload,
            "owner" to owner,
            "ledger" to ledger,
            "source" to source,
            "verified_at" to verifiedAt,
            "external_depends_on" to externalDependsOn.map { it.toMap() },
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromJson(text: String): Commitment = fromMap(parseJsonObject(text))
        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): Commitment {
            fun strings(key: String): List<String> =
                (payload[key] as? List<*>)?.map { it.toString() } ?: emptyList()

            return Commitment(
                id = payload["id"]?.toString()
                    ?: throw IllegalArgumentException("commitment id is required"),
                subject = payload["subject"]?.toString() ?: "",
                due = payload["due"]?.toString(),
                status = payload["status"]?.toString() ?: "open",
                dependsOn = strings("depends_on"),
                priority = (payload["priority"] as? Number)?.toDouble() ?: 0.5,
                payload = (payload["payload"] as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: emptyMap(),
                owner = payload["owner"]?.toString() ?: "local",
                ledger = payload["ledger"]?.toString(),
                source = payload["source"]?.toString() ?: "local",
                verifiedAt = payload["verified_at"]?.toString(),
                externalDependsOn = (payload["external_depends_on"] as? List<*>)
                    ?.mapNotNull { item ->
                        (item as? Map<*, *>)?.entries?.associate { e ->
                            e.key.toString() to e.value
                        }?.let { CommitmentRef.fromMap(it) }
                    } ?: emptyList(),
            )
        }
    }
}
