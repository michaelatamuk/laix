package dev.laix.decision.planners.composite

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
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.approvalRequired
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.time.Duration
import java.util.Locale

/** The utility, commitment, execution and attention parts of one live plan. */
data class CompositeScore(
    val utility: Double,
    val commitment: Double,
    val execution: Double,
    val humanAttention: Double,
    val total: Double,
)

/**
 * Choose the option with the best combined live score.
 *
 * The composite planner composes the four live planner scores into one decision:
 * utility, commitments, execution risk and human attention.
 */
class LiveCompositePlanner(
    private val model: UtilityModel = UtilityModel(),
    val commitmentWeights: CommitmentWeights = CommitmentWeights(),
    val executionWeights: ExecutionWeights = ExecutionWeights(),
    val humanAttentionWeights: HumanAttentionWeights = HumanAttentionWeights(),
    val enforceFeasibility: Boolean = true,
    val requireVerified: Boolean = true,
    val maxVerificationAge: Duration? = null,
) : Planner {
    val name: String = "live.v1"

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
            val blocker = constraintBlocker(problem, option)
            val score = CompositeScore(
                utility = commitment.utility,
                commitment = commitment.commitment,
                execution = execution.execution,
                humanAttention = attention.humanAttention,
                total = round6(
                    commitment.utility + commitment.commitment +
                        execution.execution + attention.humanAttention,
                ),
            )
            val blocked = commitment.blocked ?: attention.blocked ?: blocker
            Row(
                option = option,
                score = score,
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
            reasonCode = "live_decision",
            rationale = format(
                "%s balances utility %.3f, commitments %+.3f, execution %+.3f and attention %+.3f",
                best.option.id,
                best.score.utility,
                best.score.commitment,
                best.score.execution,
                best.score.humanAttention,
            ),
            actionId = best.option.id,
            requiresApproval = best.attentionScore.effect.requiresApproval ||
                best.executionScore.requiresApproval,
            reversible = best.option.reversible,
            score = best.score.total,
            alternatives = alternatives(rows, best.option.id),
            attributes = linkedMapOf(
                "utility" to best.score.utility,
                "commitment_score" to best.score.commitment,
                "execution_score" to best.score.execution,
                "human_attention_score" to best.score.humanAttention,
                "human_attention_cost" to best.attentionScore.effect.cost,
                "commitments_fulfilled" to best.commitmentScore.fulfilled,
                "commitments_violated" to best.commitmentScore.violated,
                "commitments_created" to best.commitmentScore.created,
                "receipt_status" to best.executionScore.receiptStatus,
                "approval_state" to best.attentionScore.effect.approvalState,
            ),
        )
    }

    private fun alternatives(rows: List<Row>, bestId: String): List<Map<String, Any?>> =
        rows
            .filter { it.option.id != bestId }
            .map { row ->
                val reason = when {
                    row.blocker != null -> "blocked by ${row.blocker}"
                    !row.feasible -> "outside the hard limits"
                    else -> "lower integrated score"
                }
                linkedMapOf(
                    "action_id" to row.option.id,
                    "verb" to row.option.verb.value,
                    "name" to row.option.name,
                    "utility" to row.score.utility,
                    "commitment" to row.score.commitment,
                    "execution" to row.score.execution,
                    "human_attention" to row.score.humanAttention,
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
        val score: CompositeScore,
        val feasible: Boolean,
        val blocker: String?,
        val commitmentScore: CommitmentScore,
        val executionScore: ExecutionScore,
        val attentionScore: HumanAttentionScore,
    )
}
