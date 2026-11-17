package dev.laix.decision.appkit.state

import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Goal
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.PHASES
import dev.laix.decision.contracts.SCHEMA_VERSION
import dev.laix.decision.contracts.Verb
import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.clamp
import dev.laix.decision.support.confidenceBand
import dev.laix.decision.support.iso
import dev.laix.decision.support.utcNow
import java.time.OffsetDateTime

/**
 * Experience state: goals, phase, beliefs with confidence, decay and expiry.
 *
 * This is deliberately small. It stores what the decision needs and nothing
 * about the host's database.
 */
class ExperienceState(
    val subject: String,
    var phase: String = "observe",
    val goals: MutableList<Goal> = mutableListOf(),
    val constraints: MutableList<Constraint> = mutableListOf(),
    val beliefs: LinkedHashMap<String, Belief> = LinkedHashMap(),
    val history: MutableList<Map<String, Any?>> = mutableListOf(),
    val observations: MutableList<Observation> = mutableListOf(),
) {
    init {
        require(phase in PHASES) { "unknown phase: $phase" }
    }

    /**
     * Record an observation and update a belief when it names a proposition.
     *
     * `payload["proposition"]` and `payload["confidence"]` are optional.
     */
    fun observe(observation: Observation, halfLifeMinutes: Double = 720.0): Belief? {
        observations += observation
        history += linkedMapOf(
            "at" to observation.at,
            "event" to "observed",
            "observation" to observation.id,
            "source" to observation.source,
        )
        val proposition = observation.payload["proposition"]?.toString()
        if (proposition.isNullOrEmpty()) return null
        val confidence = (observation.payload["confidence"] as? Number)?.toDouble()
            ?: (observation.payload["confidence"] as? String)?.toDoubleOrNull()
            ?: observation.normalizedConfidence
        val previous = beliefs[proposition]
        val observedAt = parseIso(observation.at)
        val merged = if (previous != null &&
            parseIso(previous.updatedAt) != null &&
            observedAt != null
        ) {
            val prior = previous.decayed(observedAt, halfLifeMinutes)
            clamp(0.55 * confidence + 0.45 * prior)
        } else {
            clamp(confidence)
        }
        val evidence = (
            listOf(observation.id) + (previous?.evidence ?: emptyList())
            ).takeLast(8)
        val belief = Belief(
            id = proposition,
            proposition = observation.payload["statement"]?.toString() ?: proposition,
            confidence = merged,
            evidence = evidence,
            updatedAt = observation.at.ifEmpty { iso() },
            expiresAt = observation.payload["expires_at"]?.toString(),
            source = observation.source,
        )
        beliefs[belief.id] = belief
        return belief
    }

    fun setBelief(belief: Belief): Belief {
        beliefs[belief.id] = belief
        history += linkedMapOf(
            "at" to iso(),
            "event" to "belief.updated",
            "belief" to belief.id,
            "confidence" to belief.confidence,
        )
        return belief
    }

    fun belief(beliefId: String): Belief? = beliefs[beliefId]

    fun confidence(beliefIds: List<String>? = null): Double {
        val items = if (beliefIds != null) {
            beliefIds.mapNotNull { beliefs[it] }
        } else {
            beliefs.values.toList()
        }
        if (items.isEmpty()) return 0.0
        return clamp(items.minOf { it.confidence })
    }

    fun band(beliefId: String): String =
        beliefs[beliefId]?.let { confidenceBand(it.confidence) } ?: "unknown"

    fun expire(now: OffsetDateTime? = null): List<String> {
        val moment = now ?: utcNow()
        val removed = beliefs.values.filter { it.expired(moment) }.map { it.id }
        for (key in removed) {
            val item = beliefs.remove(key) ?: continue
            history += linkedMapOf(
                "at" to iso(moment),
                "event" to "belief.expired",
                "belief" to key,
                "confidence" to item.confidence,
            )
        }
        return removed
    }

    fun decay(now: OffsetDateTime? = null, halfLifeMinutes: Double = 720.0) {
        val moment = now ?: utcNow()
        for ((key, item) in beliefs.entries.toList()) {
            beliefs[key] = item.copy(
                confidence = item.decayed(moment, halfLifeMinutes),
            )
        }
    }

    fun advance(phase: String) {
        require(phase in PHASES) { "unknown phase: $phase" }
        this.phase = phase
        history += linkedMapOf("at" to iso(), "event" to "phase", "phase" to phase)
    }

    fun record(decision: Decision, note: String = "") {
        history += linkedMapOf(
            "at" to decision.createdAt,
            "event" to "decision",
            "decision" to decision.decisionId,
            "verb" to decision.verb.value,
            "action" to decision.actionId,
            "note" to note,
        )
        phase = if (decision.verb in setOf(Verb.ACT, Verb.GUIDE, Verb.ASK)) "act" else "decide"
    }

    fun snapshot(): Map<String, Any?> =
        linkedMapOf(
            "subject" to subject,
            "phase" to phase,
            "goals" to goals.map { it.toMap() },
            "constraints" to constraints.map {
                linkedMapOf(
                    "id" to it.id,
                    "kind" to it.kind,
                    "value" to it.value,
                    "hard" to it.hard,
                    "statement" to it.statement,
                    "schema_version" to it.schemaVersion,
                )
            },
            "beliefs" to beliefs.values.map {
                linkedMapOf(
                    "id" to it.id,
                    "proposition" to it.proposition,
                    "confidence" to it.confidence,
                    "evidence" to it.evidence,
                    "updated_at" to it.updatedAt,
                    "expires_at" to it.expiresAt,
                    "source" to it.source,
                    "schema_version" to it.schemaVersion,
                    "band" to it.band,
                )
            },
            "history" to history,
            "observations" to observations.map { it.toMap() },
        )

    companion object {
        @Suppress("UNCHECKED_CAST")
        fun fromSnapshot(payload: Map<String, Any?>): ExperienceState {
            val state = ExperienceState(subject = payload["subject"]?.toString() ?: "")
            state.phase = payload["phase"]?.toString()?.takeIf { it in PHASES } ?: "observe"
            (payload["goals"] as? List<*>)?.forEach { item ->
                val map = (item as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: return@forEach
                state.goals += Goal(
                    id = map["id"]?.toString() ?: "",
                    statement = map["statement"]?.toString() ?: "",
                    priority = (map["priority"] as? Number)?.toDouble() ?: 0.5,
                    metric = map["metric"]?.toString() ?: "",
                    target = (map["target"] as? Number)?.toDouble(),
                    deadline = map["deadline"]?.toString(),
                    schemaVersion = map["schema_version"]?.toString() ?: SCHEMA_VERSION,
                )
            }
            (payload["constraints"] as? List<*>)?.forEach { item ->
                val map = (item as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: return@forEach
                state.constraints += Constraint(
                    id = map["id"]?.toString() ?: "",
                    kind = map["kind"]?.toString() ?: "",
                    value = map["value"],
                    hard = map["hard"] as? Boolean ?: true,
                    statement = map["statement"]?.toString() ?: "",
                    schemaVersion = map["schema_version"]?.toString() ?: SCHEMA_VERSION,
                )
            }
            (payload["beliefs"] as? List<*>)?.forEach { item ->
                val map = (item as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: return@forEach
                val belief = Belief(
                    id = map["id"]?.toString() ?: "",
                    proposition = map["proposition"]?.toString() ?: "",
                    confidence = (map["confidence"] as? Number)?.toDouble() ?: 0.0,
                    evidence = (map["evidence"] as? List<*>)?.map { it.toString() } ?: emptyList(),
                    updatedAt = map["updated_at"]?.toString() ?: iso(),
                    expiresAt = map["expires_at"]?.toString(),
                    source = map["source"]?.toString() ?: "observation",
                    schemaVersion = map["schema_version"]?.toString() ?: SCHEMA_VERSION,
                )
                state.beliefs[belief.id] = belief
            }
            (payload["history"] as? List<*>)?.forEach { item ->
                val map = (item as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: return@forEach
                state.history += map
            }
            (payload["observations"] as? List<*>)?.forEach { item ->
                val map = (item as? Map<*, *>)?.entries?.associate { e ->
                    e.key.toString() to e.value
                } ?: return@forEach
                state.observations += Observation(
                    id = map["id"]?.toString() ?: "",
                    at = map["at"]?.toString() ?: "",
                    source = map["source"]?.toString() ?: "",
                    kind = map["kind"]?.toString() ?: "",
                    confidence = (map["confidence"] as? Number)?.toDouble() ?: 0.0,
                    payload = (map["payload"] as? Map<*, *>)?.entries?.associate { e ->
                        e.key.toString() to e.value
                    } ?: emptyMap(),
                    cost = (map["cost"] as? Number)?.toDouble() ?: 0.0,
                    latencyMs = (map["latency_ms"] as? Number)?.toInt() ?: 0,
                    schemaVersion = map["schema_version"]?.toString() ?: SCHEMA_VERSION,
                )
            }
            return state
        }
    }
}

/** Storage-free state store contract. */
interface StateStore {
    fun save(key: String, state: ExperienceState)

    fun load(key: String): ExperienceState?

    fun delete(key: String)
}

/** A small in-memory store for tests and local runs. */
class InMemoryStateStore : StateStore {
    private val items = LinkedHashMap<String, ExperienceState>()

    override fun save(key: String, state: ExperienceState) {
        items[key] = state
    }

    override fun load(key: String): ExperienceState? = items[key]

    override fun delete(key: String) {
        items.remove(key)
    }
}
