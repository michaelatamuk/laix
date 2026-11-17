package dev.laix.decision.learning.causal

import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.support.round
import kotlin.math.sqrt

/** One decision, its arm and the measured outcome. */
data class CausalObservation(
    val decisionId: String,
    val arm: String,
    val outcome: Double,
    val propensity: Double? = null,
    val context: Map<String, Any?> = emptyMap(),
)

/** The estimated effect of one arm against another. */
data class CausalEffect(
    val treatment: String,
    val control: String,
    val estimate: Double,
    val treated: Int,
    val controlSize: Int,
    val method: String,
    val standardError: Double? = null,
    val ciLow: Double? = null,
    val ciHigh: Double? = null,
)

private fun variance(values: List<Double>, mean: Double): Double {
    if (values.size < 2) return 0.0
    return values.sumOf { (it - mean) * (it - mean) } / (values.size - 1)
}

private fun weightedMean(
    items: List<CausalObservation>,
    weight: (Double) -> Double,
): Double {
    var total = 0.0
    for (item in items) {
        val propensity = item.propensity
            ?: throw IllegalArgumentException("propensity is required for weighting")
        total += item.outcome * weight(propensity)
    }
    return total / items.size
}

private fun weightedVariance(
    items: List<CausalObservation>,
    weight: (Double) -> Double,
    mean: Double,
): Double {
    if (items.size < 2) return 0.0
    var total = 0.0
    for (item in items) {
        val propensity = item.propensity
            ?: throw IllegalArgumentException("propensity is required for weighting")
        val w = weight(propensity)
        total += (w * w) * ((item.outcome - mean) * (item.outcome - mean))
    }
    return total / (items.size.toDouble() * items.size)
}

/** Collect observations and estimate one treatment effect. */
class CausalLedger(
    val records: MutableList<CausalObservation> = mutableListOf(),
) {
    fun add(
        decisionId: String,
        arm: String,
        outcome: Double,
        propensity: Double? = null,
        context: Map<String, Any?> = emptyMap(),
    ): CausalObservation {
        if (propensity != null) {
            require(propensity in 0.0..1.0) { "propensity must be between zero and one" }
        }
        val observation = CausalObservation(
            decisionId = decisionId,
            arm = arm,
            outcome = outcome,
            propensity = propensity,
            context = context,
        )
        records += observation
        return observation
    }

    /**
     * Add one measured outcome to an arm.
     *
     * The measured `delta` is oriented so a positive value always means
     * improvement. For a `lower-better` metric, the sign is flipped.
     */
    fun addOutcome(
        outcome: Outcome,
        arm: String,
        propensity: Double? = null,
        context: Map<String, Any?> = emptyMap(),
        signed: Boolean = true,
    ): CausalObservation {
        var value = outcome.delta
        if (signed && outcome.direction == "lower-better") value = -value
        return add(outcome.decisionId, arm, value, propensity, context)
    }

    fun effect(treatment: String, control: String): CausalEffect {
        val treated = records.filter { it.arm == treatment }
        val controlled = records.filter { it.arm == control }
        require(treated.isNotEmpty() && controlled.isNotEmpty()) {
            "both arms need at least one observation"
        }

        val weighted = (treated + controlled).all {
            it.propensity != null && it.propensity!! > 0.0 && it.propensity!! < 1.0
        }
        val treatedMean: Double
        val controlMean: Double
        val treatedVariance: Double
        val controlVariance: Double
        val method: String
        if (weighted) {
            treatedMean = weightedMean(treated) { 1.0 / it }
            controlMean = weightedMean(controlled) { 1.0 / (1.0 - it) }
            treatedVariance = weightedVariance(treated, { 1.0 / it }, treatedMean)
            controlVariance = weightedVariance(controlled, { 1.0 / (1.0 - it) }, controlMean)
            method = "inverse-propensity"
        } else {
            treatedMean = treated.sumOf { it.outcome } / treated.size
            controlMean = controlled.sumOf { it.outcome } / controlled.size
            treatedVariance = variance(treated.map { it.outcome }, treatedMean) / treated.size
            controlVariance = variance(controlled.map { it.outcome }, controlMean) / controlled.size
            method = "difference-in-means"
        }

        val estimate = round(treatedMean - controlMean, 6)
        val standardError = round(sqrt(treatedVariance + controlVariance), 6)
        return CausalEffect(
            treatment = treatment,
            control = control,
            estimate = estimate,
            treated = treated.size,
            controlSize = controlled.size,
            method = method,
            standardError = standardError,
            ciLow = round(estimate - 1.96 * standardError, 6),
            ciHigh = round(estimate + 1.96 * standardError, 6),
        )
    }

    /** Estimate one effect per context value, skipping incomplete strata. */
    fun effectByContext(
        treatment: String,
        control: String,
        key: String = "stratum",
    ): Map<String, CausalEffect> {
        val buckets = LinkedHashMap<String, MutableList<CausalObservation>>()
        for (item in records) {
            val stratum = item.context[key]?.toString() ?: "all"
            buckets.getOrPut(stratum) { mutableListOf() } += item
        }
        val effects = LinkedHashMap<String, CausalEffect>()
        for ((stratum, items) in buckets.toSortedMap()) {
            val arms = items.map { it.arm }.toSet()
            if (treatment !in arms || control !in arms) continue
            effects[stratum] = CausalLedger(items).effect(treatment, control)
        }
        return effects
    }

    companion object {
        /** Build a ledger from outcome records and a decision-to-arm map. */
        fun fromOutcomes(
            outcomes: List<Outcome>,
            arms: Map<String, String>,
            defaultArm: String? = null,
            propensities: Map<String, Double>? = null,
            contexts: Map<String, Map<String, Any?>>? = null,
            signed: Boolean = true,
        ): CausalLedger {
            val ledger = CausalLedger()
            for (outcome in outcomes) {
                val arm = arms[outcome.decisionId] ?: defaultArm ?: continue
                ledger.addOutcome(
                    outcome,
                    arm = arm,
                    propensity = propensities?.get(outcome.decisionId),
                    context = contexts?.get(outcome.decisionId) ?: emptyMap(),
                    signed = signed,
                )
            }
            return ledger
        }
    }
}
