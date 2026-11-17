package dev.laix.decision.commitments

import dev.laix.decision.support.parseIso
import dev.laix.decision.support.parseJsonObject
import dev.laix.decision.support.toJson
import java.time.OffsetDateTime

/** An in-memory set of commitments for one task. */
class CommitmentLedger(commitments: List<Commitment> = emptyList()) {
    private val items: LinkedHashMap<String, Commitment> =
        commitments.associateByTo(LinkedHashMap()) { it.id }

    fun add(commitment: Commitment): Commitment {
        items[commitment.id] = commitment
        return commitment
    }

    fun get(commitmentId: String): Commitment =
        items[commitmentId]
            ?: throw NoSuchElementException("unknown commitment: $commitmentId")

    fun getOrNull(commitmentId: String): Commitment? = items[commitmentId]

    fun complete(commitmentId: String): Commitment = replace(commitmentId, "done")

    fun cancel(commitmentId: String): Commitment = replace(commitmentId, "cancelled")

    /** Every commitment, including done and cancelled ones. */
    fun all(): List<Commitment> = items.values.toList()

    fun open(): List<Commitment> = items.values.filter { it.status == "open" }

    fun due(now: OffsetDateTime): List<Commitment> =
        open().filter { it.isDue(now) }

    fun next(now: OffsetDateTime? = null): Commitment? {
        val openItems = open()
        if (openItems.isEmpty()) return null
        return first(openItems)
    }

    /** Return the earliest open commitment whose dependencies are complete. */
    fun nextActionable(now: OffsetDateTime? = null): Commitment? {
        val candidates = open().filter { !blocked(it) }
        if (candidates.isEmpty()) return null
        return first(candidates)
    }

    /** Return open commitments that still wait on another commitment. */
    fun blockedOpen(): List<Commitment> = open().filter { blocked(it) }

    /**
     * A local ledger cannot resolve another owner. Treat every external
     * reference as unresolved; use [CommitmentGraph] to resolve it.
     */
    fun blocked(commitment: Commitment): Boolean {
        if (commitment.externalDependsOn.isNotEmpty()) return true
        for (dependency in commitment.dependsOn) {
            val item = items[dependency]
            if (item == null || item.status != "done") return true
        }
        return false
    }

    private fun replace(commitmentId: String, status: String): Commitment {
        val item = get(commitmentId)
        val updated = item.copy(status = status)
        items[commitmentId] = updated
        return updated
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf("commitments" to items.values.map { it.toMap() })

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromJson(text: String): CommitmentLedger = fromMap(parseJsonObject(text))
        private val never: OffsetDateTime = OffsetDateTime.MAX

        private fun first(items: List<Commitment>): Commitment =
            items.sortedWith(
                compareBy(
                    { parseIso(it.due) ?: never },
                    { -it.priority },
                    { it.id },
                ),
            ).first()

        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): CommitmentLedger =
            CommitmentLedger(
                (payload["commitments"] as? List<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { e ->
                        e.key.toString() to e.value
                    }?.let { Commitment.fromMap(it) }
                } ?: emptyList(),
            )
    }
}
