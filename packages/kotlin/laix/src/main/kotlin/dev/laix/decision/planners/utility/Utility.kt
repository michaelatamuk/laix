package dev.laix.decision.planners.utility

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.asNumber
import dev.laix.decision.support.clamp
import dev.laix.decision.support.policyTruthy
import dev.laix.decision.support.round6
import java.util.Locale

enum class RiskAttitude(val value: String) {
    NEUTRAL("neutral"),
    AVERSE("averse"),
    SEEKING("seeking");

    companion object {
        fun from(value: String): RiskAttitude =
            entries.firstOrNull { it.value == value }
                ?: throw IllegalArgumentException("unknown risk attitude: $value")
    }
}

data class UtilityWeights(
    val benefit: Double = 1.0,
    val cost: Double = 0.25,
    val risk: Double = 0.25,
    val interruption: Double = 0.15,
    val latency: Double = 0.0,
) {
    init {
        require(benefit >= 0 && cost >= 0 && risk >= 0 && interruption >= 0 && latency >= 0) {
            "utility weights must not be negative"
        }
    }
}

data class UtilityModel(
    val weights: UtilityWeights = UtilityWeights(),
    val riskAttitude: RiskAttitude = RiskAttitude.NEUTRAL,
    val maxRisk: Double = 1.0,
    val maxCost: Double? = null,
    val maxLatencyMs: Double? = null,
) {
    init {
        require(maxRisk in 0.0..1.0) { "maxRisk must be between zero and one" }
    }

    fun feasible(option: ActionOption): Boolean {
        if (option.risk > maxRisk) return false
        if (maxCost != null && option.cost > maxCost) return false
        if (maxLatencyMs != null && option.latencyMs > maxLatencyMs) return false
        return true
    }

    fun score(option: ActionOption): Double {
        var risk = option.risk
        when (riskAttitude) {
            RiskAttitude.AVERSE -> risk *= 1.0 + risk
            RiskAttitude.SEEKING -> risk *= 1.0 - 0.5 * risk
            RiskAttitude.NEUTRAL -> Unit
        }
        return round6(
            weights.benefit * option.expectedBenefit -
                weights.cost * option.cost -
                weights.risk * risk -
                weights.interruption * option.interruptCost -
                weights.latency * option.latencyMs,
        )
    }
}

private fun limit(kind: String, value: Any?): Double? {
    val raw = when (value) {
        is Map<*, *> -> value["max"] ?: value["value"]
        else -> value
    }
    if (raw is Boolean || raw == null) return null
    val numeric = when (raw) {
        is Number -> raw.toDouble()
        is String -> raw.toDoubleOrNull() ?: return null
        else -> return null
    }
    return if (kind == "interruption" && numeric > 1.0) numeric / 100.0 else numeric
}

internal fun constraintBlocker(problem: PlannerInput, option: ActionOption): String? {
    val situation = problem.situation ?: return null
    val amounts = mapOf(
        "risk" to option.risk,
        "cost" to option.cost,
        "budget" to option.cost,
        "latency" to option.latencyMs.toDouble(),
        "interruption" to option.interruptCost,
    )
    for (constraint in situation.constraints) {
        if (!constraint.hard) continue
        if (constraint.kind == "safety") {
            if (policyTruthy(constraint.value)) return "safety"
            continue
        }
        val amount = amounts[constraint.kind] ?: continue
        val max = limit(constraint.kind, constraint.value) ?: continue
        if (amount > max) return "${constraint.kind}:${constraint.id}"
    }
    return null
}

internal fun approvalRequired(problem: PlannerInput): Boolean =
    problem.situation?.constraints?.any {
        it.kind == "approval" && policyTruthy(it.value)
    } ?: false

/** Resolve the model for one problem, letting request attributes override the defaults. */
internal fun utilityModelFor(problem: PlannerInput, model: UtilityModel): UtilityModel {
    val attributes = problem.attributes
    val maxRisk = asNumber(attributes["max_risk"])
    val maxCost = asNumber(attributes["max_cost"])
    val maxLatency = asNumber(attributes["max_latency_ms"])
    // Python only builds an override model when one of the hard limits is set;
    // `risk_attitude` on its own does not change the model.
    if (maxRisk == null && maxCost == null && maxLatency == null) {
        return model
    }
    return model.copy(
        riskAttitude = (attributes["risk_attitude"]?.toString() ?: model.riskAttitude.value)
            .let { RiskAttitude.from(it) },
        maxRisk = maxRisk ?: model.maxRisk,
        maxCost = maxCost ?: model.maxCost,
        maxLatencyMs = maxLatency ?: model.maxLatencyMs,
    )
}

class UtilityPlanner(
    private val model: UtilityModel = UtilityModel(),
) : Planner {
    override fun solve(problem: PlannerInput): PlannerResult {
        if (problem.options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }
        val activeModel = utilityModelFor(problem, model)
        val feasible = problem.options.filter {
            activeModel.feasible(it) && constraintBlocker(problem, it) == null
        }
        if (feasible.isEmpty()) {
            return wait("no_feasible_option", "every option is outside the hard limits")
        }

        val scored = feasible
            .map { activeModel.score(it) to it }
            .sortedWith(compareBy({ -it.first }, { it.second.id }))
        val (bestScore, best) = scored.first()
        val secondScore = scored.getOrNull(1)?.first

        return PlannerResult(
            verb = best.verb,
            confidence = confidence(bestScore, secondScore),
            reasonCode = "expected_utility",
            rationale = "${best.id} has the highest expected utility ${String.format(Locale.ROOT, "%.3f", bestScore)}",
            actionId = best.id,
            requiresApproval = best.requiresApproval || best.destructive || approvalRequired(problem),
            reversible = best.reversible,
            score = bestScore,
            alternatives = alternatives(problem, activeModel, best),
            attributes = mapOf(
                "utility" to bestScore,
                "risk_attitude" to activeModel.riskAttitude.value,
            ),
        )
    }

    private fun alternatives(
        problem: PlannerInput,
        model: UtilityModel,
        best: ActionOption,
    ): List<Map<String, Any?>> =
        problem.options
            .filter { it.id != best.id }
            .map { option ->
                val blocker = constraintBlocker(problem, option)
                val reason = when {
                    !model.feasible(option) -> "outside the hard limits"
                    blocker != null -> "blocked by $blocker"
                    else -> "lower expected utility"
                }
                mapOf(
                    "action_id" to option.id,
                    "verb" to option.verb.value,
                    "name" to option.name,
                    "utility" to model.score(option),
                    "rejected_because" to reason,
                )
            }
            .sortedWith(compareBy({ -(it["utility"] as Double) }, { it["action_id"] as String }))

    private fun wait(reasonCode: String, rationale: String): PlannerResult =
        PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = reasonCode,
            rationale = rationale,
            score = 0.0,
        )

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }
}
