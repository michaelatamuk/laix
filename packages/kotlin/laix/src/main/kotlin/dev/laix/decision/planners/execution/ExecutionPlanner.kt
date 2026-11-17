package dev.laix.decision.planners.execution

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.approvalRequired
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.util.Locale

/** The execution facts that change an option's score. */
@ConsistentCopyVisibility
data class ExecutionEffect private constructor(
    val unknownRisk: Double,
    val recoveryCost: Double,
) {
    companion object {
        operator fun invoke(unknownRisk: Double = 0.0, recoveryCost: Double = 0.0): ExecutionEffect =
            ExecutionEffect(clamp(unknownRisk), maxOf(0.0, recoveryCost))
    }
}

/** How much each execution risk subtracts from the utility score. */
data class ExecutionWeights(
    val irreversible: Double = 0.35,
    val unknown: Double = 0.5,
    val approval: Double = 0.15,
    val recovery: Double = 0.25,
) {
    init {
        for ((name, value) in listOf(
            "irreversible" to irreversible,
            "unknown" to unknown,
            "approval" to approval,
            "recovery" to recovery,
        )) {
            require(value >= 0) { "execution weight '$name' must not be negative" }
        }
    }
}

/** The utility and execution parts of one option's score. */
data class ExecutionScore(
    val utility: Double,
    val execution: Double,
    val total: Double,
    val irreversible: Boolean = false,
    val unknownRisk: Double = 0.0,
    val recoveryCost: Double = 0.0,
    val requiresApproval: Boolean = false,
    val receiptStatus: String? = null,
    val blocked: String? = null,
)

/**
 * Read an option's execution facts from `params`.
 *
 * Supported shapes:
 *
 * ```
 * params = mapOf("execution" to mapOf("unknown_risk" to 0.4, "recovery_cost" to 0.2))
 * params = mapOf("unknown_risk" to 0.4, "recovery_cost" to 0.2)
 * ```
 */
fun executionEffect(option: ActionOption): ExecutionEffect {
    val params = option.params
    val payload = (params["execution"] as? Map<*, *>) ?: params
    fun value(key: String): Double {
        val raw = payload[key] ?: params[key] ?: 0.0
        return when (raw) {
            is Number -> raw.toDouble()
            is String -> raw.toDoubleOrNull() ?: 0.0
            else -> 0.0
        }
    }
    return ExecutionEffect(unknownRisk = value("unknown_risk"), recoveryCost = value("recovery_cost"))
}

/** Choose the option with the best utility plus execution risk. */
class ExecutionRiskPlanner(
    private val model: UtilityModel = UtilityModel(),
    val weights: ExecutionWeights = ExecutionWeights(),
) : Planner {
    val name: String = "execution.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model)
        val approval = approvalRequired(problem)
        val rows = options.map { option ->
            val score = scoreOption(option, activeModel, weights, approval, receiptStatus(problem, option))
            val blocker = constraintBlocker(problem, option)
            Row(
                option = option,
                score = score,
                feasible = activeModel.feasible(option) && blocker == null,
                blocker = blocker,
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            return wait("no_feasible_option", "every option is outside the hard limits")
        }

        val ranked = feasible.sortedWith(compareBy({ -it.score.total }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.score?.total

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.score.total, second),
            reasonCode = "execution_aware",
            rationale = format(
                "%s balances utility %.3f and execution cost %+.3f",
                best.option.id,
                best.score.utility,
                best.score.execution,
            ),
            actionId = best.option.id,
            requiresApproval = best.option.requiresApproval || best.option.destructive || approval,
            reversible = best.option.reversible,
            score = best.score.total,
            alternatives = alternatives(rows, best.option.id),
            attributes = linkedMapOf(
                "utility" to best.score.utility,
                "execution_score" to best.score.execution,
                "irreversible" to best.score.irreversible,
                "unknown_risk" to best.score.unknownRisk,
                "recovery_cost" to best.score.recoveryCost,
                "requires_approval" to best.score.requiresApproval,
                "receipt_status" to best.score.receiptStatus,
            ),
        )
    }

    internal fun scoreOption(
        option: ActionOption,
        model: UtilityModel,
        weights: ExecutionWeights,
        approval: Boolean,
        receiptStatus: String?,
    ): ExecutionScore {
        val effect = executionEffect(option)
        val irreversible = !option.reversible
        var requiresApproval = approval || option.requiresApproval || option.destructive
        var unknownRisk = effect.unknownRisk
        var recoveryCost = effect.recoveryCost
        when (receiptStatus) {
            "unknown" -> unknownRisk = maxOf(unknownRisk, 1.0)
            "failed", "refused", "cancelled", "undone" -> recoveryCost = maxOf(recoveryCost, 1.0)
            "pending" -> requiresApproval = true
        }
        val execution =
            -weights.irreversible * (if (irreversible) 1.0 else 0.0) -
                weights.unknown * unknownRisk -
                weights.approval * (if (requiresApproval) 1.0 else 0.0) -
                weights.recovery * recoveryCost
        val utilityScore = model.score(option)
        return ExecutionScore(
            utility = round6(utilityScore),
            execution = round6(execution),
            total = round6(utilityScore + execution),
            irreversible = irreversible,
            unknownRisk = unknownRisk,
            recoveryCost = recoveryCost,
            requiresApproval = requiresApproval,
            receiptStatus = receiptStatus,
        )
    }

    private fun alternatives(rows: List<Row>, bestId: String): List<Map<String, Any?>> =
        rows
            .filter { it.option.id != bestId }
            .map { row ->
                val reason = when {
                    row.blocker != null -> "blocked by ${row.blocker}"
                    !row.feasible -> "outside the hard limits"
                    else -> "lower execution-adjusted score"
                }
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.score.utility,
                    "execution" to row.score.execution,
                    "total" to row.score.total,
                    "rejected_because" to reason,
                )
            }
            .sortedWith(compareBy({ -(it["total"] as Double) }, { it["action_id"] as String }))

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }

    private fun wait(reasonCode: String, rationale: String): PlannerResult =
        PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = reasonCode,
            rationale = rationale,
            score = 0.0,
        )

    private fun format(pattern: String, vararg args: Any): String =
        String.format(Locale.ROOT, pattern, *args)

    private data class Row(
        val option: ActionOption,
        val score: ExecutionScore,
        val feasible: Boolean,
        val blocker: String?,
    )

    companion object {
        internal fun receiptStatus(problem: PlannerInput, option: ActionOption): String? {
            val attributes = problem.attributes
            val raw = attributes["execution_state"]
            if (raw is Map<*, *>) {
                return (raw[option.id] ?: raw[option.name])?.toString()
            }
            val receipts = attributes["execution_receipts"] as? Iterable<*> ?: return null
            for (item in receipts) {
                if (item is Map<*, *>) {
                    val name = item["action_name"]
                    val status = item["status"]
                    if ((name == option.id || name == option.name) && status != null) {
                        return status.toString()
                    }
                }
            }
            return null
        }
    }
}
