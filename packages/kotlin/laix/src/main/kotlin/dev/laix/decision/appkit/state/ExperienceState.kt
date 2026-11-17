package dev.laix.decision.appkit.state

import dev.laix.decision.contracts.Belief
import dev.laix.decision.contracts.Constraint
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Goal
import dev.laix.decision.contracts.Observation
import dev.laix.decision.contracts.PHASES
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.clamp
import dev.laix.decision.support.confidenceBand
import dev.laix.decision.support.iso
import dev.laix.decision.support.parseIso
import dev.laix.decision.support.toJson
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
            ?: observation.confidence
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
            beliefs[key] = item.withConfidence(item.decayed(moment, halfLifeMinutes))
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
            "constraints" to constraints.map { it.toMap() },
            "beliefs" to beliefs.values.map { it.toMap() },
            "history" to history,
            "observations" to observations.map { it.toMap() },
        )

    /** Python's `ExperienceState.to_dict`: beliefs are a map and carry no band. */
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "subject" to subject,
            "phase" to phase,
            "goals" to goals.map { it.toMap() },
            "constraints" to constraints.map { it.toMap() },
            "beliefs" to beliefs.values.associate { belief ->
                belief.id to linkedMapOf(
                    "id" to belief.id,
                    "proposition" to belief.proposition,
                    "confidence" to belief.confidence,
                    "evidence" to belief.evidence,
                    "updated_at" to belief.updatedAt,
                    "expires_at" to belief.expiresAt,
                    "source" to belief.source,
                    "schema_version" to belief.schemaVersion,
                )
            },
            "history" to history,
            "observations" to observations.map { it.toMap() },
        )

    fun toJson(pretty: Boolean = false): String = toMap().toJson(pretty)

    companion object {
        fun fromSnapshot(payload: Map<String, Any?>): ExperienceState {
            fun map(value: Any?): Map<String, Any?>? =
                (value as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }

            val state = ExperienceState(subject = payload["subject"]?.toString() ?: "")
            state.phase = payload["phase"]?.toString()?.takeIf { it in PHASES } ?: "observe"
            (payload["goals"] as? Iterable<*>)?.forEach { item ->
                map(item)?.let { state.goals += Goal.fromMap(it) }
            }
            (payload["constraints"] as? Iterable<*>)?.forEach { item ->
                map(item)?.let { state.constraints += Constraint.fromMap(it) }
            }
            (payload["beliefs"] as? Iterable<*>)?.forEach { item ->
                map(item)?.let {
                    val belief = Belief.fromMap(it)
                    state.beliefs[belief.id] = belief
                }
            }
            (payload["history"] as? Iterable<*>)?.forEach { item ->
                map(item)?.let { state.history += it }
            }
            (payload["observations"] as? Iterable<*>)?.forEach { item ->
                map(item)?.let { state.observations += Observation.fromMap(it) }
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
