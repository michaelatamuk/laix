package dev.laix.decision.planners.risk

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.util.Locale

/** Choose the best option whose downside stays inside a hard limit. */
class RiskBoundedPlanner(
    private val model: UtilityModel = UtilityModel(),
    val maxLoss: Double = 0.5,
    val penalty: Double = 0.0,
) : Planner {
    init {
        require(maxLoss >= 0) { "max_loss must not be negative" }
        require(penalty >= 0) { "penalty must not be negative" }
    }

    val name: String = "risk_bounded.v1"

    private val utility: UtilityPlanner = UtilityPlanner(model)

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model)
        val rows = options.map { option ->
            val utilityScore = activeModel.score(option)
            val worst = risk(option, "worst_case_loss", option.risk)
            val cvar = risk(option, "cvar_loss", worst)
            val feasible = activeModel.feasible(option) && cvar <= maxLoss
            Row(
                option = option,
                utility = round6(utilityScore),
                worstCaseLoss = round6(worst),
                cvarLoss = round6(cvar),
                total = round6(utilityScore - penalty * clamp(cvar)),
                feasible = feasible,
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            return wait(
                "no_feasible_option",
                "every option exceeds the downside limit",
                mapOf("risk_limit" to maxLoss),
            )
        }

        val ranked = feasible.sortedWith(compareBy({ -it.total }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.total
        val alternatives = rows
            .filter { it.option.id != best.option.id }
            .map { row ->
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.utility,
                    "total" to row.total,
                    "cvar_loss" to row.cvarLoss,
                    "rejected_reason_code" to if (!row.feasible) {
                        "risk_limit"
                    } else {
                        "lower_risk_adjusted_score"
                    },
                )
            }

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.total, second),
            reasonCode = "risk_bounded",
            rationale = format(
                "%s keeps CVaR %.3f within %.3f",
                best.option.id,
                best.cvarLoss,
                maxLoss,
            ),
            actionId = best.option.id,
            requiresApproval = best.option.requiresApproval,
            reversible = best.option.reversible,
            score = best.total,
            alternatives = alternatives,
            attributes = linkedMapOf(
                "risk_limit" to maxLoss,
                "worst_case_loss" to best.worstCaseLoss,
                "cvar_loss" to best.cvarLoss,
                "utility" to best.utility,
            ),
        )
    }

    private fun wait(
        reasonCode: String,
        rationale: String,
        attributes: Map<String, Any?> = emptyMap(),
    ): PlannerResult =
        PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = reasonCode,
            rationale = rationale,
            score = 0.0,
            attributes = attributes,
        )

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }

    private fun format(pattern: String, vararg args: Any): String =
        String.format(Locale.ROOT, pattern, *args)

    private data class Row(
        val option: ActionOption,
        val utility: Double,
        val worstCaseLoss: Double,
        val cvarLoss: Double,
        val total: Double,
        val feasible: Boolean,
    )

    private companion object {
        fun risk(option: ActionOption, key: String, fallback: Double): Double {
            val params = option.params
            val payload = when (val raw = params["risk_bound"] ?: params["risk"]) {
                is Map<*, *> -> raw
                else -> emptyMap<Any?, Any?>()
            }
            val value = payload[key] ?: params[key] ?: fallback
            return when (value) {
                is Number -> value.toDouble()
                is String -> value.toDoubleOrNull() ?: fallback
                else -> fallback
            }
        }
    }
}
