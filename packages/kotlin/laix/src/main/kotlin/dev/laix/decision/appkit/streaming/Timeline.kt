package dev.laix.decision.appkit.streaming

import dev.laix.decision.contracts.Decision

/** An error raised when a decision breaks timeline semantics. */
class TimelineError(message: String) : IllegalArgumentException(message)

/** A compact view of one timeline. */
data class TimelineReport(
    val decisions: Int,
    val chains: Int,
    val superseded: Int,
    val issues: List<String>,
) {
    val valid: Boolean
        get() = issues.isEmpty()

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "decisions" to decisions,
            "chains" to chains,
            "superseded" to superseded,
            "valid" to valid,
            "issues" to issues,
        )
}

/** An append-only timeline with revision and event-time rules. */
class DecisionTimeline(decisions: List<Decision> = emptyList()) {
    private val byId = LinkedHashMap<String, Decision>()
    private val order = mutableListOf<String>()

    init {
        decisions.forEach { add(it) }
    }

    /** Append one decision or raise [TimelineError]. */
    fun add(decision: Decision): Decision {
        val decisionId = decision.decisionId
        if (decisionId.isEmpty()) throw TimelineError("decision id is required")
        if (byId.containsKey(decisionId)) {
            throw TimelineError("duplicate decision id: $decisionId")
        }

        val revision = decision.revision
        val previousId = decision.supersedes
        if (revision < 0) throw TimelineError("negative revision: $decisionId")
        if (revision == 0 && !previousId.isNullOrEmpty()) {
            throw TimelineError("root decision $decisionId cannot supersede $previousId")
        }
        if (revision > 0) {
            if (previousId.isNullOrEmpty()) {
                throw TimelineError("revision $revision of $decisionId needs a predecessor")
            }
            val previous = byId[previousId]
                ?: throw TimelineError("unknown predecessor $previousId for $decisionId")
            if (previous.revision + 1 != revision) {
                throw TimelineError(
                    "revision $revision of $decisionId must follow ${previous.revision}",
                )
            }
            if (previous.streamId.isNotEmpty() &&
                decision.streamId.isNotEmpty() &&
                previous.streamId != decision.streamId
            ) {
                throw TimelineError(
                    "stream mismatch: ${previous.streamId} -> ${decision.streamId}",
                )
            }
            if (!previous.eventTime.isNullOrEmpty() &&
                !decision.eventTime.isNullOrEmpty() &&
                decision.eventTime < previous.eventTime
            ) {
                throw TimelineError(
                    "event time moved backwards: ${previous.eventTime} -> ${decision.eventTime}",
                )
            }
        }

        byId[decisionId] = decision
        order += decisionId
        return decision
    }

    fun get(decisionId: String): Decision =
        byId[decisionId] ?: throw TimelineError("unknown decision: $decisionId")

    fun all(): List<Decision> = order.map { byId.getValue(it) }

    /** Return the chain from the root to [decisionId]. */
    fun history(decisionId: String): List<Decision> {
        val chain = mutableListOf<Decision>()
        val seen = mutableSetOf<String>()
        var current: String? = decisionId
        while (current != null) {
            if (current in seen) throw TimelineError("cycle at $current")
            seen += current
            val decision = get(current)
            chain += decision
            current = decision.supersedes
        }
        return chain.reversed()
    }

    fun supersededIds(): Set<String> =
        byId.values.mapNotNull { it.supersedes }.toSet()

    fun isSuperseded(decisionId: String): Boolean = decisionId in supersededIds()

    /** Return the latest decision in each chain. */
    fun current(streamId: String? = null): List<Decision> {
        val superseded = supersededIds()
        return all().filter {
            it.decisionId !in superseded &&
                (streamId == null || it.streamId == streamId)
        }
    }

    /** Return the last appended decision, optionally for one stream. */
    fun latest(streamId: String? = null): Decision? =
        order.reversed().map { byId.getValue(it) }
            .firstOrNull { streamId == null || it.streamId == streamId }

    /** Return decisions whose event time is before [watermark]. */
    fun late(watermark: String): List<Decision> =
        all().filter { !it.eventTime.isNullOrEmpty() && it.eventTime < watermark }

    /** Re-check stored decisions and return every issue found. */
    fun issues(): List<String> {
        val issues = mutableListOf<String>()
        for (decision in all()) {
            if (decision.decisionId.isEmpty()) {
                issues += "decision id is required"
                continue
            }
            if (decision.revision == 0) {
                if (!decision.supersedes.isNullOrEmpty()) {
                    issues += "root ${decision.decisionId} supersedes ${decision.supersedes}"
                }
                continue
            }
            val previous = byId[decision.supersedes ?: ""]
            if (previous == null) {
                issues += "missing predecessor ${decision.supersedes} for ${decision.decisionId}"
                continue
            }
            if (previous.revision + 1 != decision.revision) {
                issues += "revision gap ${previous.revision} -> ${decision.revision} " +
                    "at ${decision.decisionId}"
            }
            if (previous.streamId.isNotEmpty() &&
                decision.streamId.isNotEmpty() &&
                previous.streamId != decision.streamId
            ) {
                issues += "stream mismatch at ${decision.decisionId}: " +
                    "${previous.streamId} -> ${decision.streamId}"
            }
            if (!previous.eventTime.isNullOrEmpty() &&
                !decision.eventTime.isNullOrEmpty() &&
                decision.eventTime < previous.eventTime
            ) {
                issues += "event time backwards at ${decision.decisionId}"
            }
        }
        return issues
    }

    fun assertValid() {
        val issues = issues()
        if (issues.isNotEmpty()) throw TimelineError(issues.joinToString("; "))
    }

    fun report(): TimelineReport {
        val superseded = supersededIds()
        val roots = all().count { it.decisionId !in superseded }
        return TimelineReport(
            decisions = byId.size,
            chains = roots,
            superseded = superseded.size,
            issues = issues(),
        )
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf("decisions" to all().map { it.toMap() })

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromMap(payload: Map<String, Any?>): DecisionTimeline =
            DecisionTimeline(
                (payload["decisions"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                        ?.let { Decision.fromMap(it) }
                } ?: emptyList(),
            )
    }
}
