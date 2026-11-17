package dev.laix.decision.planners.explain

import dev.laix.decision.contracts.Decision
import dev.laix.decision.support.round6
import java.util.Locale

private val COMPONENT_KEYS: Map<String, String> = linkedMapOf(
    "utility" to "utility",
    "commitment" to "commitment_score",
    "execution" to "execution_score",
    "human_attention" to "human_attention_score",
)

private val ALTERNATIVE_KEYS: Map<String, String> = linkedMapOf(
    "utility" to "utility",
    "commitment" to "commitment",
    "execution" to "execution",
    "human_attention" to "human_attention",
)

/** One sufficient single-component change. */
data class Counterfactual(
    val alternativeId: String,
    val component: String,
    val delta: Double,
    val chosenTotal: Double,
    val alternativeTotal: Double,
    val resultingTotal: Double,
    val explanation: String,
)

/** Ranked counterfactuals for one decision. */
data class CounterfactualReport(
    val chosenId: String,
    val chosenTotal: Double,
    val counterfactuals: List<Counterfactual>,
    val minimal: Counterfactual?,
)

/**
 * Return the smallest single-component changes that flip the decision.
 *
 * `decision.attributes` must carry the component scores, and each alternative
 * must carry the matching component keys. This is true for decisions produced
 * by the live composite and value-of-decision planners.
 */
fun counterfactualAttribution(
    decision: Decision,
    components: List<String>? = null,
    margin: Double = 1e-6,
): CounterfactualReport {
    val chosenId = decision.actionId ?: "chosen"
    val chosenTotal = decision.score ?: 0.0
    val attributes = decision.attributes
    val requested = components ?: COMPONENT_KEYS.keys.toList()
    val available = requested.filter {
        COMPONENT_KEYS.containsKey(it) && attributes.containsKey(COMPONENT_KEYS.getValue(it))
    }
    if (available.isEmpty() || decision.alternatives.isEmpty()) {
        return CounterfactualReport(
            chosenId = chosenId,
            chosenTotal = round6(chosenTotal),
            counterfactuals = emptyList(),
            minimal = null,
        )
    }

    val rows = mutableListOf<Counterfactual>()
    for (alternative in decision.alternatives) {
        val alternativeId = (alternative["action_id"] ?: alternative["actionId"])?.toString() ?: ""
        val alternativeTotal = number(alternative["total"]) ?: 0.0
        val gap = chosenTotal - alternativeTotal
        if (gap <= 0) continue
        for (component in available) {
            val alternativeKey = ALTERNATIVE_KEYS.getValue(component)
            if (alternative[alternativeKey] == null) continue
            val delta = round6(maxOf(0.0, gap + margin))
            rows += Counterfactual(
                alternativeId = alternativeId,
                component = component,
                delta = delta,
                chosenTotal = round6(chosenTotal),
                alternativeTotal = round6(alternativeTotal),
                resultingTotal = round6(alternativeTotal + delta),
                explanation = String.format(
                    Locale.ROOT,
                    "%s overtakes %s if %s increases by %.6f",
                    alternativeId,
                    chosenId,
                    component,
                    delta,
                ),
            )
        }
    }

    rows.sortWith(compareBy({ it.delta }, { it.alternativeId }, { it.component }))
    return CounterfactualReport(
        chosenId = chosenId,
        chosenTotal = round6(chosenTotal),
        counterfactuals = rows,
        minimal = rows.firstOrNull(),
    )
}

private fun number(value: Any?): Double? =
    when (value) {
        is Number -> value.toDouble()
        is String -> value.toDoubleOrNull()
        else -> null
    }
