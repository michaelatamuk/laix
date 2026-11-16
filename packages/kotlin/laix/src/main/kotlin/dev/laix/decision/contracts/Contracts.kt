package dev.laix.decision.contracts

import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6

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

data class Belief(
    val id: String,
    val proposition: String,
    val confidence: Double,
    val evidence: List<String> = emptyList(),
    val updatedAt: String = "",
    val expiresAt: String? = null,
    val source: String = "observation",
    val schemaVersion: String = SCHEMA_VERSION,
) {
    init {
        require(confidence in 0.0..1.0) { "belief confidence must be between zero and one" }
    }

    val band: String
        get() = when {
            confidence >= 0.8 -> "high"
            confidence >= 0.55 -> "medium"
            else -> "low"
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
        ): ActionOption =
            ActionOption(
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
    }
}

data class Situation(
    val id: String,
    val at: String,
    val subject: String,
    val observations: List<Any?> = emptyList(),
    val beliefs: List<Belief> = emptyList(),
    val goals: List<Any?> = emptyList(),
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
        val value = attributes["confidence"]
        return clamp((value as? Number)?.toDouble() ?: 0.0)
    }

    fun uncertainty(): Double {
        val value = attributes["uncertainty"]
        return clamp((value as? Number)?.toDouble() ?: (1.0 - confidence()))
    }
}

data class Intent(
    val capability: String,
    val args: Map<String, Any?> = emptyMap(),
)
