package dev.laix.decision.contracts

import dev.laix.decision.support.asNumber
import dev.laix.decision.support.clamp
import dev.laix.decision.support.iso
import dev.laix.decision.support.parseIso
import dev.laix.decision.support.round6
import dev.laix.decision.support.truthy
import dev.laix.decision.support.utcNow
import java.time.OffsetDateTime

const val SCHEMA_VERSION = "0.8.0"

enum class Verb(val value: String) {
    WAIT("wait"),
    OBSERVE("observe"),
    GUIDE("guide"),
    ASK("ask"),
    ACT("act"),
    VERIFY("verify"),
    ESCALATE("escalate");

    companion object {
        val values: List<String> = entries.map { it.value }

        fun from(value: String): Verb =
            entries.firstOrNull { it.value == value }
                ?: throw IllegalArgumentException("unknown verb: $value")
    }
}

val VERBS: List<String> = Verb.values

val CONSTRAINT_KINDS: List<String> = listOf(
    "latency",
    "cost",
    "risk",
    "interruption",
    "approval",
    "safety",
    "budget",
    "policy",
)

val PHASES: List<String> = listOf("observe", "understand", "decide", "act", "verify", "adapt")

val HORIZONS: List<String> = listOf("seconds", "minutes", "hours", "days", "weeks")

@ConsistentCopyVisibility
data class Belief private constructor(
    val id: String,
    val proposition: String,
    val confidence: Double,
    val evidence: List<String>,
    val updatedAt: String,
    val expiresAt: String?,
    val source: String,
    val schemaVersion: String,
) {
    val band: String
        get() = when {
            confidence >= 0.8 -> "high"
            confidence >= 0.55 -> "medium"
            else -> "low"
        }

    fun expired(now: OffsetDateTime? = null): Boolean {
        val expires = parseIso(expiresAt) ?: return false
        val moment = now ?: utcNow()
        return !expires.toInstant().isAfter(moment.toInstant())
    }

    fun decayed(now: OffsetDateTime? = null, halfLifeMinutes: Double = 720.0): Double {
        val updated = parseIso(updatedAt) ?: return confidence
        if (halfLifeMinutes <= 0) return confidence
        val elapsed = java.time.Duration.between(updated, now ?: utcNow()).toMillis() / 60_000.0
        if (elapsed <= 0) return confidence
        return clamp(confidence * Math.pow(0.5, elapsed / halfLifeMinutes))
    }

    /** A copy with a clamped confidence; the data-class copy is private. */
    fun withConfidence(value: Double): Belief =
        invoke(
            id = id,
            proposition = proposition,
            confidence = value,
            evidence = evidence,
            updatedAt = updatedAt,
            expiresAt = expiresAt,
            source = source,
            schemaVersion = schemaVersion,
        )

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "proposition" to proposition,
            "confidence" to confidence,
            "evidence" to evidence,
            "updated_at" to updatedAt,
            "expires_at" to expiresAt,
            "source" to source,
            "schema_version" to schemaVersion,
            "band" to band,
        )

    companion object {
        /** Mirrors Python: confidence is clamped, not rejected. */
        operator fun invoke(
            id: String,
            proposition: String,
            confidence: Double,
            evidence: List<String> = emptyList(),
            updatedAt: String = iso(),
            expiresAt: String? = null,
            source: String = "observation",
            schemaVersion: String = SCHEMA_VERSION,
        ): Belief = create(
            id,
            proposition,
            clamp(confidence),
            evidence,
            updatedAt,
            expiresAt,
            source,
            schemaVersion,
        )

        private fun create(
            id: String,
            proposition: String,
            confidence: Double,
            evidence: List<String>,
            updatedAt: String,
            expiresAt: String?,
            source: String,
            schemaVersion: String,
        ): Belief = Belief(
            id = id,
            proposition = proposition,
            confidence = confidence,
            evidence = evidence,
            updatedAt = updatedAt,
            expiresAt = expiresAt,
            source = source,
            schemaVersion = schemaVersion,
        )

        fun fromMap(payload: Map<String, Any?>): Belief =
            invoke(
                id = payload["id"]?.toString() ?: "",
                proposition = payload["proposition"]?.toString() ?: "",
                confidence = asNumber(payload["confidence"]) ?: 0.0,
                evidence = (payload["evidence"] as? Iterable<*>)?.map { it.toString() } ?: emptyList(),
                updatedAt = payload["updated_at"]?.toString() ?: iso(),
                expiresAt = payload["expires_at"]?.toString(),
                source = payload["source"]?.toString() ?: "observation",
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

data class Constraint(
    val id: String,
    val kind: String,
    val value: Any?,
    val hard: Boolean = true,
    val statement: String = "",
    val schemaVersion: String = SCHEMA_VERSION,
) {
    init {
        require(kind in CONSTRAINT_KINDS) { "unknown constraint kind: $kind" }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "kind" to kind,
            "value" to value,
            "hard" to hard,
            "statement" to statement,
            "schema_version" to schemaVersion,
        )

    companion object {
        fun fromMap(payload: Map<String, Any?>): Constraint =
            Constraint(
                id = payload["id"]?.toString() ?: "",
                kind = payload["kind"]?.toString()
                    ?: throw IllegalArgumentException("constraint kind is required"),
                value = payload["value"],
                hard = payload["hard"]?.let { truthy(it) } ?: true,
                statement = payload["statement"]?.toString() ?: "",
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

@ConsistentCopyVisibility
data class ActionOption private constructor(
    val id: String,
    val verb: Verb,
    val name: String,
    val params: Map<String, Any?>,
    val expectedBenefit: Double,
    val cost: Double,
    val risk: Double,
    val latencyMs: Int,
    val interruptCost: Double,
    val destructive: Boolean,
    val reversible: Boolean,
    val requiresApproval: Boolean,
    val addresses: List<String>,
    val rationale: String,
    val schemaVersion: String,
) {
    val utility: Double
        get() = round6(expectedBenefit - 0.25 * risk - 0.15 * interruptCost)

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "verb" to verb.value,
            "name" to name,
            "params" to params,
            "expected_benefit" to expectedBenefit,
            "cost" to cost,
            "risk" to risk,
            "latency_ms" to latencyMs,
            "interrupt_cost" to interruptCost,
            "destructive" to destructive,
            "reversible" to reversible,
            "requires_approval" to requiresApproval,
            "addresses" to addresses,
            "rationale" to rationale,
            "schema_version" to schemaVersion,
            "utility" to utility,
        )

    companion object {
        /** Mirrors the Python constructor: out-of-range scores are clamped, not rejected. */
        operator fun invoke(
            id: String,
            verb: Verb,
            name: String,
            params: Map<String, Any?> = emptyMap(),
            expectedBenefit: Double = 0.5,
            cost: Double = 0.0,
            risk: Double = 0.0,
            latencyMs: Int = 0,
            interruptCost: Double = 0.0,
            destructive: Boolean = false,
            reversible: Boolean = true,
            requiresApproval: Boolean = false,
            addresses: List<String> = emptyList(),
            rationale: String = "",
            schemaVersion: String = SCHEMA_VERSION,
        ): ActionOption = create(
            id = id,
            verb = verb,
            name = name,
            params = params,
            expectedBenefit = clamp(expectedBenefit),
            cost = cost,
            risk = clamp(risk),
            latencyMs = latencyMs,
            interruptCost = clamp(interruptCost),
            destructive = destructive,
            reversible = reversible,
            requiresApproval = requiresApproval || destructive,
            addresses = addresses,
            rationale = rationale,
            schemaVersion = schemaVersion,
        )

        private fun create(
            id: String,
            verb: Verb,
            name: String,
            params: Map<String, Any?>,
            expectedBenefit: Double,
            cost: Double,
            risk: Double,
            latencyMs: Int,
            interruptCost: Double,
            destructive: Boolean,
            reversible: Boolean,
            requiresApproval: Boolean,
            addresses: List<String>,
            rationale: String,
            schemaVersion: String,
        ): ActionOption = ActionOption(
            id = id,
            verb = verb,
            name = name,
            params = params,
            expectedBenefit = expectedBenefit,
            cost = cost,
            risk = risk,
            latencyMs = latencyMs,
            interruptCost = interruptCost,
            destructive = destructive,
            reversible = reversible,
            requiresApproval = requiresApproval,
            addresses = addresses,
            rationale = rationale,
            schemaVersion = schemaVersion,
        )

        fun fromMap(payload: Map<String, Any?>): ActionOption =
            invoke(
                id = payload["id"]?.toString() ?: "",
                verb = Verb.from(payload["verb"]?.toString() ?: Verb.ACT.value),
                name = payload["name"]?.toString() ?: "",
                params = (payload["params"] as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                    ?: emptyMap(),
                expectedBenefit = asNumber(payload["expected_benefit"]) ?: 0.5,
                cost = asNumber(payload["cost"]) ?: 0.0,
                risk = asNumber(payload["risk"]) ?: 0.0,
                latencyMs = asNumber(payload["latency_ms"])?.toInt() ?: 0,
                interruptCost = asNumber(payload["interrupt_cost"]) ?: 0.0,
                destructive = payload["destructive"]?.let { truthy(it) } ?: false,
                reversible = payload["reversible"]?.let { truthy(it) } ?: true,
                requiresApproval = payload["requires_approval"]?.let { truthy(it) } ?: false,
                addresses = (payload["addresses"] as? Iterable<*>)?.map { it.toString() } ?: emptyList(),
                rationale = payload["rationale"]?.toString() ?: "",
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

data class Situation(
    val id: String,
    val at: String,
    val subject: String,
    val observations: List<Observation> = emptyList(),
    val beliefs: List<Belief> = emptyList(),
    val goals: List<Goal> = emptyList(),
    val constraints: List<Constraint> = emptyList(),
    val phase: String = "observe",
    val horizon: String = "minutes",
    val attributes: Map<String, Any?> = emptyMap(),
    val schemaVersion: String = SCHEMA_VERSION,
) {
    init {
        require(phase in PHASES) { "unknown phase: $phase" }
        require(horizon in HORIZONS) { "unknown horizon: $horizon" }
    }

    fun belief(id: String): Belief? = beliefs.firstOrNull { it.id == id }

    fun constraint(kind: String): Constraint? = constraints.firstOrNull { it.kind == kind }

    fun confidence(): Double {
        if (beliefs.isNotEmpty()) return clamp(beliefs.minOf { it.confidence })
        return clamp(asNumber(attributes["confidence"]) ?: 0.0)
    }

    fun uncertainty(): Double =
        clamp(asNumber(attributes["uncertainty"]) ?: (1.0 - confidence()))

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "at" to at,
            "subject" to subject,
            "observations" to observations.map { it.toMap() },
            "beliefs" to beliefs.map { it.toMap() },
            "goals" to goals.map { it.toMap() },
            "constraints" to constraints.map { it.toMap() },
            "phase" to phase,
            "horizon" to horizon,
            "attributes" to attributes,
            "schema_version" to schemaVersion,
        )

    companion object {
        fun fromMap(payload: Map<String, Any?>): Situation =
            Situation(
                id = payload["id"]?.toString() ?: "",
                at = payload["at"]?.toString() ?: "",
                subject = payload["subject"]?.toString() ?: "",
                observations = (payload["observations"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                        ?.let { Observation.fromMap(it) }
                } ?: emptyList(),
                beliefs = (payload["beliefs"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                        ?.let { Belief.fromMap(it) }
                } ?: emptyList(),
                goals = (payload["goals"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                        ?.let { Goal.fromMap(it) }
                } ?: emptyList(),
                constraints = (payload["constraints"] as? Iterable<*>)?.mapNotNull { item ->
                    (item as? Map<*, *>)?.entries?.associate { it.key.toString() to it.value }
                        ?.let { Constraint.fromMap(it) }
                } ?: emptyList(),
                phase = payload["phase"]?.toString() ?: "observe",
                horizon = payload["horizon"]?.toString() ?: "minutes",
                attributes = (payload["attributes"] as? Map<*, *>)?.entries?.associate {
                    it.key.toString() to it.value
                } ?: emptyMap(),
                schemaVersion = payload["schema_version"]?.toString() ?: SCHEMA_VERSION,
            )
    }
}

data class Intent(
    val capability: String,
    val args: Map<String, Any?> = emptyMap(),
) {
    fun asDict(): Map<String, Any?> =
        linkedMapOf("capability" to capability, "args" to args)
}
