package dev.laix.decision.planners.decisionvalue

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.attention.HumanAttentionPlanner
import dev.laix.decision.planners.attention.HumanAttentionScore
import dev.laix.decision.planners.attention.HumanAttentionWeights
import dev.laix.decision.planners.attention.approvalState
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.commitment.CommitmentScore
import dev.laix.decision.planners.commitment.CommitmentWeights
import dev.laix.decision.planners.commitment.activeAndGraph
import dev.laix.decision.planners.commitment.plannerNow
import dev.laix.decision.planners.execution.ExecutionRiskPlanner
import dev.laix.decision.planners.execution.ExecutionScore
import dev.laix.decision.planners.execution.ExecutionWeights
import dev.laix.decision.planners.pomdp.PomdpModel
import dev.laix.decision.planners.pomdp.actionFutureValue
import dev.laix.decision.planners.pomdp.beliefEntropy
import dev.laix.decision.planners.pomdp.beliefFromState
import dev.laix.decision.planners.pomdp.normalizeBelief
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.approvalRequired
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.time.Duration
import java.util.Locale

/** Weights for the one-step value-of-decision terms. */
data class CAVODWeights(
    val information: Double = 0.5,
    val waiting: Double = 0.25,
    val uncertainty: Double = 0.5,
    val future: Double = 1.0,
) {
    init {
        for ((name, value) in listOf(
            "information" to information,
            "waiting" to waiting,
            "uncertainty" to uncertainty,
            "future" to future,
        )) {
            require(value >= 0) { "CA-VOD weight '$name' must not be negative" }
        }
    }
}

/** The four live terms plus the information, option and future values. */
data class CAVODScore(
    val utility: Double,
    val commitment: Double,
    val execution: Double,
    val humanAttention: Double,
    val information: Double,
    val option: Double,
    val future: Double,
    val total: Double,
)

private val INFORMATION_GAIN: Map<Verb, Double> = mapOf(
    Verb.ASK to 0.7,
    Verb.VERIFY to 0.5,
    Verb.OBSERVE to 0.4,
)

private fun decisionValue(option: ActionOption): Map<*, *> {
    val params = option.params
    val payload = params["decision_value"] ?: params["value"]
    return payload as? Map<*, *> ?: emptyMap<Any?, Any?>()
}

private fun uncertainty(problem: PlannerInput, weights: CAVODWeights): Double {
    val raw = problem.attributes["uncertainty"]
    if (raw != null) {
        val numeric = when (raw) {
            is Number -> raw.toDouble()
            is String -> raw.toDoubleOrNull()
            else -> null
        }
        if (numeric != null) return clamp(numeric)
    }
    problem.situation?.let { return clamp(1.0 - it.confidence()) }
    return clamp(weights.uncertainty)
}

private fun informationValue(
    option: ActionOption,
    uncertainty: Double,
    weights: CAVODWeights,
): Double {
    val payload = decisionValue(option)
    val explicit = payload["information_value"]
    if (explicit != null) {
        val numeric = when (explicit) {
            is Number -> explicit.toDouble()
            is String -> explicit.toDoubleOrNull()
            else -> null
        }
        if (numeric != null) return round6(maxOf(0.0, numeric))
    }
    val rawGain = payload["information_gain"]
    val gain = when (rawGain) {
        is Number -> maxOf(0.0, rawGain.toDouble())
        is String -> maxOf(0.0, rawGain.toDoubleOrNull() ?: 0.0)
        else -> INFORMATION_GAIN[option.verb] ?: 0.0
    }
    return round6(weights.information * uncertainty * gain)
}

private fun optionValue(
    option: ActionOption,
    uncertainty: Double,
    weights: CAVODWeights,
): Double {
    if (option.verb != Verb.WAIT) return 0.0
    val payload = decisionValue(option)
    val explicit = payload["option_value"]
    if (explicit != null) {
        val numeric = when (explicit) {
            is Number -> explicit.toDouble()
            is String -> explicit.toDoubleOrNull()
            else -> null
        }
        if (numeric != null) return round6(maxOf(0.0, numeric))
    }
    return round6(weights.waiting * uncertainty)
}

/**
 * Choose the option with the best one-step value of decision.
 *
 * The planner composes the same four live terms as [dev.laix.decision.planners.composite.LiveCompositePlanner]
 * and adds:
 *
 * - `information` for verbs that reduce uncertainty;
 * - `option` for `wait`;
 * - `future` when a [PomdpModel] and a belief are supplied.
 */
class CAVODPlanner(
    private val model: UtilityModel = UtilityModel(),
    val pomdpModel: PomdpModel? = null,
    belief: Map<String, Double> = emptyMap(),
    val weights: CAVODWeights = CAVODWeights(),
    val commitmentWeights: CommitmentWeights = CommitmentWeights(),
    val executionWeights: ExecutionWeights = ExecutionWeights(),
    val humanAttentionWeights: HumanAttentionWeights = HumanAttentionWeights(),
    val enforceFeasibility: Boolean = true,
    val requireVerified: Boolean = true,
    val maxVerificationAge: Duration? = null,
) : Planner {
    val name: String = "ca_vod.v1"
    val belief: Map<String, Double> = belief.toMap()

    private val commitmentPlanner = CommitmentPlanner(
        model = model,
        weights = commitmentWeights,
        requireVerified = requireVerified,
        maxVerificationAge = maxVerificationAge,
    )
    private val executionPlanner = ExecutionRiskPlanner(model, executionWeights)
    private val attentionPlanner = HumanAttentionPlanner(model, humanAttentionWeights)

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model)
        val (commitments, graph) = activeAndGraph(problem)
        val now = plannerNow(problem)
        val approval = approvalRequired(problem)
        val remaining = HumanAttentionPlanner.remaining(problem)
        val uncertaintyValue = uncertainty(problem, weights)
        val resolvedBelief = if (pomdpModel != null) resolveBelief(problem) else emptyMap()
        val horizon = if (pomdpModel != null) {
            (problem.attributes["horizon"] as? Number)?.toInt() ?: pomdpModel.horizon
        } else {
            0
        }

        fun isBlocked(commitmentId: String): Boolean {
            val commitment: Commitment = commitments[commitmentId] ?: return true
            return graph.blocked(
                commitment,
                requireVerified = requireVerified,
                now = now,
                maxVerificationAge = maxVerificationAge,
            )
        }

        val rows = options.map { option ->
            val commitment = commitmentPlanner.scoreOption(option, activeModel, commitments, now, ::isBlocked)
            val execution = executionPlanner.scoreOption(
                option,
                activeModel,
                executionWeights,
                approval,
                ExecutionRiskPlanner.receiptStatus(problem, option),
            )
            val attention = attentionPlanner.scoreOption(
                option,
                activeModel,
                humanAttentionWeights,
                remaining,
                approval,
                approvalState(problem, option),
            )
            val information = informationValue(option, uncertaintyValue, weights)
            val optionScore = optionValue(option, uncertaintyValue, weights)
            val future = futureValue(option, resolvedBelief, horizon)
            val blocker = constraintBlocker(problem, option)
            val total = round6(
                commitment.utility + commitment.commitment +
                    execution.execution + attention.humanAttention +
                    information + optionScore + future,
            )
            val blocked = commitment.blocked ?: attention.blocked ?: blocker
            Row(
                option = option,
                score = CAVODScore(
                    utility = commitment.utility,
                    commitment = commitment.commitment,
                    execution = execution.execution,
                    humanAttention = attention.humanAttention,
                    information = information,
                    option = optionScore,
                    future = future,
                    total = total,
                ),
                feasible = if (enforceFeasibility) {
                    activeModel.feasible(option) && blocked == null
                } else {
                    true
                },
                blocker = blocked,
                commitmentScore = commitment,
                executionScore = execution,
                attentionScore = attention,
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            return wait(
                "no_feasible_option",
                "every option breaks a hard limit or an attention constraint",
            )
        }

        val ranked = feasible.sortedWith(compareBy({ -it.score.total }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.score?.total

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.score.total, second),
            reasonCode = "value_of_decision",
            rationale = format(
                "%s balances utility %.3f, commitment %+.3f, execution %+.3f, attention %+.3f, " +
                    "information %+.3f, option value %+.3f and future value %+.3f",
                best.option.id,
                best.score.utility,
                best.score.commitment,
                best.score.execution,
                best.score.humanAttention,
                best.score.information,
                best.score.option,
                best.score.future,
            ),
            actionId = best.option.id,
            requiresApproval = best.attentionScore.effect.requiresApproval ||
                best.executionScore.requiresApproval,
            reversible = best.option.reversible,
            score = best.score.total,
            alternatives = alternatives(rows, best.option.id),
            attributes = linkedMapOf(
                "algorithm" to name,
                "utility" to best.score.utility,
                "commitment_score" to best.score.commitment,
                "execution_score" to best.score.execution,
                "human_attention_score" to best.score.humanAttention,
                "information_value" to best.score.information,
                "option_value" to best.score.option,
                "future_value" to best.score.future,
                "uncertainty" to uncertaintyValue,
                "belief" to resolvedBelief.ifEmpty { null },
                "belief_entropy" to if (resolvedBelief.isNotEmpty()) beliefEntropy(resolvedBelief) else null,
                "horizon" to if (pomdpModel != null) horizon else null,
                "commitments_fulfilled" to best.commitmentScore.fulfilled,
                "commitments_violated" to best.commitmentScore.violated,
                "commitments_created" to best.commitmentScore.created,
                "receipt_status" to best.executionScore.receiptStatus,
                "approval_state" to best.attentionScore.effect.approvalState,
            ),
        )
    }

    private fun resolveBelief(problem: PlannerInput): Map<String, Double> {
        val pomdp = pomdpModel ?: return emptyMap()
        val raw = problem.attributes["belief"]
        if (raw is Map<*, *>) {
            val numeric = LinkedHashMap<String, Double>()
            for ((key, value) in raw) {
                val number = when (value) {
                    is Number -> value.toDouble()
                    is String -> value.toDoubleOrNull()
                    else -> null
                }
                if (number != null) numeric[key.toString()] = number
            }
            return normalizeBelief(numeric, pomdp.states)
        }
        if (belief.isNotEmpty()) return normalizeBelief(belief, pomdp.states)
        val state = problem.attributes["state"] as? String
        if (!state.isNullOrEmpty()) return beliefFromState(state, pomdp.states)
        val size = pomdp.states.size
        return pomdp.states.associateWith { 1.0 / size }
    }

    private fun actionFor(option: ActionOption): String? {
        val pomdp = pomdpModel ?: return null
        if (option.id in pomdp.actions) return option.id
        if (option.verb.value in pomdp.actions) return option.verb.value
        return null
    }

    private fun futureValue(
        option: ActionOption,
        belief: Map<String, Double>,
        horizon: Int,
    ): Double {
        val pomdp = pomdpModel ?: return 0.0
        if (belief.isEmpty()) return 0.0
        val action = actionFor(option) ?: return 0.0
        if (belief.keys.none { pomdp.actionAvailable(it, action) }) return 0.0
        return round6(weights.future * actionFutureValue(pomdp, belief, action, horizon))
    }

    private fun alternatives(rows: List<Row>, bestId: String): List<Map<String, Any?>> =
        rows
            .filter { it.option.id != bestId }
            .map { row ->
                val reason = when {
                    row.blocker != null -> "blocked by ${row.blocker}"
                    !row.feasible -> "outside the hard limits"
                    else -> "lower value of decision"
                }
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.score.utility,
                    "commitment" to row.score.commitment,
                    "execution" to row.score.execution,
                    "human_attention" to row.score.humanAttention,
                    "information" to row.score.information,
                    "option" to row.score.option,
                    "future" to row.score.future,
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
        val score: CAVODScore,
        val feasible: Boolean,
        val blocker: String?,
        val commitmentScore: CommitmentScore,
        val executionScore: ExecutionScore,
        val attentionScore: HumanAttentionScore,
    )
}
