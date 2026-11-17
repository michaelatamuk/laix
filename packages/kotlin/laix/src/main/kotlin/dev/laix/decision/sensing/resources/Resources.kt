package dev.laix.decision.sensing.resources

import dev.laix.decision.support.clamp
import java.util.Locale

/** Resource limits for perception and model calls. */
data class Budget(
    val maxDeepCalls: Int = 4,
    val maxCost: Double = 1.0,
    val maxLatencyMs: Int = 2_000,
)

/** One perception or model call the scheduler can admit. */
@ConsistentCopyVisibility
data class SensingOption private constructor(
    val name: String,
    val tier: String,
    val cost: Double,
    val latencyMs: Int,
    val informationGain: Double,
) {
    companion object {
        operator fun invoke(
            name: String,
            tier: String = "cheap",
            cost: Double = 0.0,
            latencyMs: Int = 0,
            informationGain: Double = 0.0,
        ): SensingOption {
            require(tier in setOf("cheap", "deep")) { "unknown sensing tier: $tier" }
            return create(name, tier, cost, latencyMs, clamp(informationGain))
        }

        private fun create(
            name: String,
            tier: String,
            cost: Double,
            latencyMs: Int,
            informationGain: Double,
        ): SensingOption = SensingOption(name, tier, cost, latencyMs, informationGain)
    }
}

/** What the resource scheduler admitted and what it skipped. */
data class ResourcePlan(
    val allowed: List<String>,
    val skipped: List<Map<String, Any?>>,
    val deepCalls: Int,
    val cost: Double,
    val reason: String,
    val attributes: Map<String, Any?> = emptyMap(),
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "allowed" to allowed,
            "skipped" to skipped,
            "deepCalls" to deepCalls,
            "cost" to dev.laix.decision.support.round(cost, 6),
            "reason" to reason,
            "attributes" to attributes,
        )
}

/**
 * Resource policy: which perception or model call is worth making.
 *
 * Cheap detectors run continuously; a deep call is admitted only when its
 * expected information gain, weighted by the current uncertainty, clears a
 * threshold and the budget still allows it.
 */
class ResourceScheduler(
    val minInformationGain: Double = 0.35,
) {
    fun schedule(
        options: List<SensingOption>,
        budget: Budget? = null,
        uncertainty: Double = 0.5,
    ): ResourcePlan {
        val limits = budget ?: Budget()
        val clamped = clamp(uncertainty)
        val allowed = mutableListOf<String>()
        val skipped = mutableListOf<Map<String, Any?>>()
        var deepCalls = 0
        var cost = 0.0

        for (option in options) {
            if (option.tier == "cheap") {
                allowed += option.name
                cost += option.cost
                continue
            }
            val gain = option.informationGain * maxOf(clamped, 0.05)
            val reason = when {
                deepCalls >= limits.maxDeepCalls -> "deep-call budget exhausted"
                cost + option.cost > limits.maxCost -> "cost budget exhausted"
                option.latencyMs > limits.maxLatencyMs -> "latency budget exceeded"
                gain < minInformationGain -> String.format(
                    Locale.ROOT,
                    "information gain %.2f below threshold %.2f",
                    gain,
                    minInformationGain,
                )
                else -> null
            }
            if (reason != null) {
                skipped += linkedMapOf(
                    "name" to option.name,
                    "reason" to reason,
                    "gain" to dev.laix.decision.support.round(gain, 3),
                )
                continue
            }
            allowed += option.name
            deepCalls++
            cost += option.cost
        }

        return ResourcePlan(
            allowed = allowed,
            skipped = skipped,
            deepCalls = deepCalls,
            cost = cost,
            reason = "cheap continuous; deep calls admitted by gain, uncertainty and budget",
            attributes = linkedMapOf(
                "uncertainty" to dev.laix.decision.support.round(clamped, 3),
                "threshold" to minInformationGain,
            ),
        )
    }

    companion object {
        /** The cheap model is not sure enough; ask for the expensive one. */
        fun shouldEscalate(confidence: Double, required: Double = 0.75): Boolean =
            clamp(confidence) < clamp(required)
    }
}
