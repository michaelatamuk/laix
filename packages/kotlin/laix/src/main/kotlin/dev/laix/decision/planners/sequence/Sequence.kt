package dev.laix.decision.planners.sequence

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.planners.attention.HumanAttentionBudget
import dev.laix.decision.planners.attention.HumanAttentionPlanner
import dev.laix.decision.planners.attention.HumanAttentionWeights
import dev.laix.decision.planners.commitment.CommitmentPlanner
import dev.laix.decision.planners.commitment.CommitmentWeights
import dev.laix.decision.planners.execution.ExecutionRiskPlanner
import dev.laix.decision.planners.execution.ExecutionWeights
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.round6
import dev.laix.decision.support.utcNow
import java.time.Duration
import java.time.OffsetDateTime

/** The options available at one moment in the sequence. */
data class DecisionStep(
    val at: String,
    val options: List<ActionOption>,
)

/** A finite deterministic decision sequence. */
data class DecisionScenario(
    val steps: List<DecisionStep>,
    val commitments: List<Commitment> = emptyList(),
    val humanAttentionBudget: HumanAttentionBudget? = null,
    val openPenalty: Double = 0.5,
)

/** The chosen option at each step and the search evidence. */
data class DecisionPlan(
    val actions: List<String>,
    val score: Double,
    val attentionSpent: Double,
    val violations: List<String>,
    val nodes: Int,
    val optimal: Boolean,
)

/** A planner that chooses a chain of actions, not one live decision. */
interface SequencePlanner {
    val name: String

    fun plan(scenario: DecisionScenario): DecisionPlan
}

/** Exact branch-and-bound planning for a finite decision sequence. */
class CABBPlanner(
    val model: UtilityModel = UtilityModel(),
    val commitmentWeights: CommitmentWeights = CommitmentWeights(),
    val executionWeights: ExecutionWeights = ExecutionWeights(),
    val humanAttentionWeights: HumanAttentionWeights = HumanAttentionWeights(),
    val requireVerified: Boolean = true,
    val maxVerificationAge: Duration? = null,
) : SequencePlanner {
    override val name: String = "cabb.v1"

    private val commitmentPlanner = CommitmentPlanner(
        model = model,
        weights = commitmentWeights,
        requireVerified = requireVerified,
        maxVerificationAge = maxVerificationAge,
    )
    private val executionPlanner = ExecutionRiskPlanner(model, executionWeights)
    private val attentionPlanner = HumanAttentionPlanner(model, humanAttentionWeights)

    override fun plan(scenario: DecisionScenario): DecisionPlan {
        if (scenario.steps.isEmpty()) {
            return DecisionPlan(emptyList(), 0.0, 0.0, emptyList(), 0, true)
        }
        val statuses = scenario.commitments.associateTo(LinkedHashMap()) { it.id to it.status }
        val initialAttention = initialAttention(scenario)
        val finalAt = parseIso(scenario.steps.last().at) ?: utcNow()
        val commitmentCeiling = scenario.commitments.sumOf {
            commitmentWeights.keep * (0.5 + it.priority) +
                commitmentWeights.due * (0.5 + it.priority)
        }
        val bounds = scenario.steps.map { relaxedBound(it, commitmentCeiling) }

        var bestScore = Double.NEGATIVE_INFINITY
        var bestActions: List<String> = emptyList()
        var bestRemaining = initialAttention
        var bestViolations: List<String> = emptyList()
        var nodes = 0

        fun search(
            index: Int,
            current: Map<String, String>,
            remaining: Double,
            score: Double,
            actions: List<String>,
            violations: List<String>,
        ) {
            nodes++
            if (index == scenario.steps.size) {
                val total = score - terminalPenalty(scenario, current, finalAt)
                if (total > bestScore) {
                    bestScore = total
                    bestActions = actions
                    bestRemaining = remaining
                    bestViolations = violations
                }
                return
            }
            if (score + bounds.drop(index).sum() <= bestScore) return
            val step = scenario.steps[index]
            val now = parseIso(step.at) ?: utcNow()
            for (option in step.options) {
                val scored = score(scenario, option, current, remaining, now)
                if (scored.blocked) continue
                search(
                    index + 1,
                    apply(current, scored),
                    scored.remaining,
                    score + scored.immediate,
                    actions + option.id,
                    violations + scored.violated,
                )
            }
        }

        search(0, statuses, initialAttention, 0.0, emptyList(), emptyList())
        if (bestScore == Double.NEGATIVE_INFINITY) {
            return DecisionPlan(emptyList(), 0.0, 0.0, emptyList(), nodes, true)
        }
        val spent = if (initialAttention != Double.POSITIVE_INFINITY) {
            initialAttention - bestRemaining
        } else {
            0.0
        }
        return DecisionPlan(
            actions = bestActions,
            score = round6(bestScore),
            attentionSpent = round6(spent),
            violations = bestViolations,
            nodes = nodes,
            optimal = true,
        )
    }

    /** Replay a fixed action sequence with the CABB score. */
    fun evaluate(scenario: DecisionScenario, actions: List<String>): DecisionPlan {
        require(actions.size == scenario.steps.size) {
            "actions must match the number of steps"
        }
        if (scenario.steps.isEmpty()) {
            return DecisionPlan(emptyList(), 0.0, 0.0, emptyList(), 0, false)
        }
        var statuses = scenario.commitments.associateTo(LinkedHashMap()) { it.id to it.status }
        val initialAttention = initialAttention(scenario)
        var remaining = initialAttention
        var score = 0.0
        val violations = mutableListOf<String>()
        val finalAt = parseIso(scenario.steps.last().at) ?: utcNow()
        for ((step, actionId) in scenario.steps.zip(actions)) {
            val option = step.options.firstOrNull { it.id == actionId }
                ?: throw IllegalArgumentException("unknown action '$actionId' at ${step.at}")
            val now = parseIso(step.at) ?: utcNow()
            val scored = score(scenario, option, statuses, remaining, now)
            if (scored.blocked) {
                throw IllegalArgumentException("action '$actionId' is blocked at ${step.at}")
            }
            score += scored.immediate
            statuses = LinkedHashMap(apply(statuses, scored))
            violations += scored.violated
            remaining = scored.remaining
        }
        val penalty = terminalPenalty(scenario, statuses, finalAt)
        val spent = if (initialAttention != Double.POSITIVE_INFINITY) {
            initialAttention - remaining
        } else {
            0.0
        }
        return DecisionPlan(
            actions = actions,
            score = round6(score - penalty),
            attentionSpent = round6(spent),
            violations = violations,
            nodes = 0,
            optimal = false,
        )
    }

    /** Complete a scenario by taking the best immediate option at each step. */
    fun greedyActions(
        scenario: DecisionScenario,
        prefix: List<String> = emptyList(),
    ): List<String> {
        require(prefix.size <= scenario.steps.size) { "the prefix is longer than the scenario" }
        var statuses = scenario.commitments.associateTo(LinkedHashMap()) { it.id to it.status }
        var remaining = initialAttention(scenario)
        val actions = prefix.toMutableList()
        for ((step, actionId) in scenario.steps.zip(prefix)) {
            val option = step.options.firstOrNull { it.id == actionId }
                ?: throw IllegalArgumentException("unknown action '$actionId' at ${step.at}")
            val now = parseIso(step.at) ?: utcNow()
            val scored = score(scenario, option, statuses, remaining, now)
            statuses = LinkedHashMap(apply(statuses, scored))
            remaining = scored.remaining
        }
        for (step in scenario.steps.drop(prefix.size)) {
            val now = parseIso(step.at) ?: utcNow()
            var best: Scored? = null
            for (option in step.options) {
                val scored = score(scenario, option, statuses, remaining, now)
                if (scored.blocked) continue
                if (best == null ||
                    scored.immediate > best.immediate ||
                    (scored.immediate == best.immediate && option.id < best.option.id)
                ) {
                    best = scored
                }
            }
            val chosen = best ?: break
            actions += chosen.option.id
            statuses = LinkedHashMap(apply(statuses, chosen))
            remaining = chosen.remaining
        }
        return actions
    }

    /** Return commitments and remaining attention after a fixed prefix. */
    fun advance(
        scenario: DecisionScenario,
        actions: List<String>,
    ): Pair<List<Commitment>, Double> {
        require(actions.size <= scenario.steps.size) { "the prefix is longer than the scenario" }
        var statuses = scenario.commitments.associateTo(LinkedHashMap()) { it.id to it.status }
        var remaining = initialAttention(scenario)
        for ((step, actionId) in scenario.steps.zip(actions)) {
            val option = step.options.firstOrNull { it.id == actionId }
                ?: throw IllegalArgumentException("unknown action '$actionId' at ${step.at}")
            val now = parseIso(step.at) ?: utcNow()
            val scored = score(scenario, option, statuses, remaining, now)
            statuses = LinkedHashMap(apply(statuses, scored))
            remaining = scored.remaining
        }
        val commitments = scenario.commitments.map {
            it.copy(status = statuses.getValue(it.id))
        }
        return commitments to remaining
    }

    private fun score(
        scenario: DecisionScenario,
        option: ActionOption,
        statuses: Map<String, String>,
        remaining: Double,
        now: OffsetDateTime,
    ): Scored {
        val current = scenario.commitments.map {
            it.copy(status = statuses[it.id] ?: it.status)
        }
        val commitments = current.associateBy { it.id }
        val local = CommitmentLedger(current.filter { it.owner == "local" })
        val external = current.filter { it.owner != "local" }
        val graph = CommitmentGraph(local, external)

        fun isBlocked(commitmentId: String): Boolean {
            val item = commitments[commitmentId] ?: return true
            return graph.blocked(
                item,
                requireVerified = requireVerified,
                now = now,
                maxVerificationAge = maxVerificationAge,
            )
        }

        val commitment = commitmentPlanner.scoreOption(option, model, commitments, now, ::isBlocked)
        val execution = executionPlanner.scoreOption(option, model, executionWeights, false, null)
        val attention = attentionPlanner.scoreOption(
            option,
            model,
            humanAttentionWeights,
            remaining,
            false,
            null,
        )
        return Scored(
            option = option,
            immediate = commitment.utility + commitment.commitment +
                execution.execution + attention.humanAttention,
            remaining = attention.remaining,
            fulfilled = commitment.fulfilled,
            violated = commitment.violated,
            blocked = commitment.blocked != null || attention.blocked != null,
        )
    }

    private fun apply(statuses: Map<String, String>, scored: Scored): Map<String, String> {
        val updated = LinkedHashMap(statuses)
        for (commitmentId in scored.fulfilled) updated[commitmentId] = "done"
        for (commitmentId in scored.violated) updated[commitmentId] = "cancelled"
        return updated
    }

    private fun initialAttention(scenario: DecisionScenario): Double =
        scenario.humanAttentionBudget?.remaining() ?: Double.POSITIVE_INFINITY

    private fun terminalPenalty(
        scenario: DecisionScenario,
        statuses: Map<String, String>,
        finalAt: OffsetDateTime,
    ): Double {
        val commitments = scenario.commitments.associateBy { it.id }
        var penalty = 0.0
        for ((commitmentId, status) in statuses) {
            if (status != "open") continue
            val item = commitments[commitmentId] ?: continue
            val due = parseIso(item.due)
            if (due == null || !due.toInstant().isAfter(finalAt.toInstant())) {
                penalty += scenario.openPenalty * (0.5 + item.priority)
            }
        }
        return penalty
    }

    private fun relaxedBound(step: DecisionStep, commitmentCeiling: Double): Double {
        if (step.options.isEmpty()) return 0.0
        return step.options.maxOf { model.score(it) } + commitmentCeiling
    }

    private data class Scored(
        val option: ActionOption,
        val immediate: Double,
        val remaining: Double,
        val fulfilled: List<String>,
        val violated: List<String>,
        val blocked: Boolean,
    )
}

/** Approximate finite-horizon planning by one-step rollout. */
class RolloutPlanner(
    val planner: CABBPlanner = CABBPlanner(),
) : SequencePlanner {
    override val name: String = "sequence.rollout.v1"

    override fun plan(scenario: DecisionScenario): DecisionPlan {
        if (scenario.steps.isEmpty()) {
            return DecisionPlan(emptyList(), 0.0, 0.0, emptyList(), 0, true)
        }
        var best: DecisionPlan? = null
        var nodes = 0
        for (option in scenario.steps.first().options) {
            val actions = planner.greedyActions(scenario, listOf(option.id))
            if (actions.size != scenario.steps.size) continue
            val result = try {
                planner.evaluate(scenario, actions)
            } catch (_: IllegalArgumentException) {
                continue
            }
            nodes++
            if (best == null ||
                result.score > best.score ||
                (result.score == best.score && lexicographicallySmaller(result.actions, best.actions))
            ) {
                best = result
            }
        }
        val chosen = best ?: return DecisionPlan(emptyList(), 0.0, 0.0, emptyList(), nodes, false)
        return DecisionPlan(
            actions = chosen.actions,
            score = chosen.score,
            attentionSpent = chosen.attentionSpent,
            violations = chosen.violations,
            nodes = nodes,
            optimal = false,
        )
    }
}

/** Functional shortcut for one rollout plan. */
fun rolloutDecisions(scenario: DecisionScenario): DecisionPlan = RolloutPlanner().plan(scenario)

/** The executed prefix and the newly planned suffix. */
data class ReplanResult(
    val executed: List<String>,
    val actions: List<String>,
    val score: Double,
    val attentionSpent: Double,
    val violations: List<String>,
    val nodes: Int,
    val optimal: Boolean,
    val reason: String,
)

/** Recompute the remaining chain from the state after a prefix. */
class ReplanPlanner(
    val planner: CABBPlanner = CABBPlanner(),
) {
    val name: String = "sequence.replan.v1"

    fun replan(
        scenario: DecisionScenario,
        executed: List<String>,
        replacementStep: DecisionStep? = null,
    ): ReplanResult {
        val prefix = executed.toList()
        require(prefix.size <= scenario.steps.size) {
            "the executed prefix is longer than the scenario"
        }
        val (commitments, remaining) = planner.advance(scenario, prefix)
        val steps = scenario.steps.drop(prefix.size).toMutableList()
        if (replacementStep != null && steps.isNotEmpty()) steps[0] = replacementStep
        if (steps.isEmpty()) {
            return ReplanResult(
                executed = prefix,
                actions = emptyList(),
                score = 0.0,
                attentionSpent = 0.0,
                violations = emptyList(),
                nodes = 0,
                optimal = true,
                reason = "nothing left to replan",
            )
        }
        val budget = scenario.humanAttentionBudget
        val nextBudget = budget?.let {
            HumanAttentionBudget(
                total = it.total,
                spent = maxOf(0.0, it.total - remaining),
            )
        }
        val nextScenario = DecisionScenario(
            steps = steps,
            commitments = commitments,
            humanAttentionBudget = nextBudget,
            openPenalty = scenario.openPenalty,
        )
        val plan = planner.plan(nextScenario)
        return ReplanResult(
            executed = prefix,
            actions = plan.actions,
            score = plan.score,
            attentionSpent = plan.attentionSpent,
            violations = plan.violations,
            nodes = plan.nodes,
            optimal = plan.optimal,
            reason = "replanned ${steps.size} remaining steps",
        )
    }
}

/** Functional shortcut for one replan. */
fun replanDecisions(
    scenario: DecisionScenario,
    executed: List<String>,
): ReplanResult = ReplanPlanner().replan(scenario, executed)

/** Functional shortcut for one CABB plan. */
fun planDecisions(scenario: DecisionScenario): DecisionPlan = CABBPlanner().plan(scenario)

private fun lexicographicallySmaller(left: List<String>, right: List<String>): Boolean {
    for (index in 0 until minOf(left.size, right.size)) {
        val comparison = left[index].compareTo(right[index])
        if (comparison != 0) return comparison < 0
    }
    return left.size < right.size
}
