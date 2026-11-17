package dev.laix.decision.planners.commitment

import dev.laix.decision.commitments.Commitment
import dev.laix.decision.commitments.CommitmentGraph
import dev.laix.decision.commitments.CommitmentLedger
import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.utility.UtilityModel
import dev.laix.decision.planners.utility.UtilityPlanner
import dev.laix.decision.planners.utility.approvalRequired
import dev.laix.decision.planners.utility.constraintBlocker
import dev.laix.decision.planners.utility.utilityModelFor
import dev.laix.decision.signals.parseIso
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import dev.laix.decision.support.utcNow
import java.time.Duration
import java.time.OffsetDateTime
import java.util.Locale

/**
 * Choose the option with the best utility plus commitment effect.
 *
 * The planner keeps the ordinary utility score and adds the effect of an action
 * on open commitments: fulfilling a promise, breaking one, or creating a new one.
 * It is deliberately deterministic and training-free; the commitments and their
 * due times come from the host.
 */
class CommitmentPlanner(
    private val model: UtilityModel? = null,
    val weights: CommitmentWeights = CommitmentWeights(),
    val requireVerified: Boolean = true,
    val maxVerificationAge: Duration? = null,
) : Planner {
    val name: String = "commitment.v1"

    private val utility: UtilityPlanner = UtilityPlanner(model ?: UtilityModel())

    override fun solve(problem: PlannerInput): PlannerResult {
        val options = problem.options
        if (options.isEmpty()) {
            return wait("no_options", "there are no options to score")
        }

        val activeModel = utilityModelFor(problem, model ?: UtilityModel())
        val (active, graph) = activeAndGraph(problem)
        val now = plannerNow(problem)

        fun blocked(commitmentId: String): Boolean {
            val commitment = active[commitmentId] ?: return true
            return graph.blocked(
                commitment,
                requireVerified = requireVerified,
                now = now,
                maxVerificationAge = maxVerificationAge,
            )
        }

        val rows = options.map { option ->
            val score = scoreOption(option, activeModel, active, now, ::blocked)
            val blocker = constraintBlocker(problem, option)
            val feasible = activeModel.feasible(option) && blocker == null && score.blocked == null
            Row(
                option = option,
                score = score,
                feasible = feasible,
                blocker = score.blocked ?: blocker,
                blockedBy = optionBlockers(
                    option = option,
                    active = active,
                    graph = graph,
                    requireVerified = requireVerified,
                    now = now,
                    maxVerificationAge = maxVerificationAge,
                ),
            )
        }

        val feasible = rows.filter { it.feasible }
        if (feasible.isEmpty()) {
            return wait(
                "no_feasible_option",
                "every option breaks a hard limit or a hard commitment",
            )
        }

        val ranked = feasible.sortedWith(compareBy({ -it.score.total }, { it.option.id }))
        val best = ranked.first()
        val second = ranked.getOrNull(1)?.score?.total

        return PlannerResult(
            verb = best.option.verb,
            confidence = confidence(best.score.total, second),
            reasonCode = "commitment_aware",
            rationale = format(
                "%s balances utility %.3f and commitment score %+.3f",
                best.option.id,
                best.score.utility,
                best.score.commitment,
            ),
            actionId = best.option.id,
            requiresApproval = best.option.requiresApproval ||
                best.option.destructive ||
                approvalRequired(problem),
            reversible = best.option.reversible,
            score = best.score.total,
            alternatives = alternatives(rows, best.option.id),
            attributes = linkedMapOf(
                "utility" to best.score.utility,
                "commitment_score" to best.score.commitment,
                "commitments_fulfilled" to best.score.fulfilled,
                "commitments_violated" to best.score.violated,
                "commitments_created" to best.score.created,
                "commitments_due_fulfilled" to best.score.dueFulfilled,
                "commitments_blocked_fulfilled" to best.score.blockedFulfilled,
                "commitments_blocked_by" to best.blockedBy,
            ),
        )
    }

    internal fun scoreOption(
        option: ActionOption,
        model: UtilityModel,
        active: Map<String, Commitment>,
        now: OffsetDateTime,
        blocked: (String) -> Boolean,
    ): CommitmentScore {
        val effect = commitmentEffect(option)
        val openIds = active.filterValues { it.status == "open" }.keys
        val fulfilled = effect.fulfills.filter { it in openIds && !blocked(it) }
        val blockedFulfilled = effect.fulfills.filter { it in openIds && blocked(it) }
        val violated = effect.violates.filter { it in openIds }
        val created = effect.creates.filter { it !in active }
        val dueFulfilled = fulfilled.filter { active.getValue(it).isDue(now) }
        val dueViolated = violated.filter { active.getValue(it).isDue(now) }
        val keepReward = fulfilled.sumOf { weights.keep * (0.5 + active.getValue(it).priority) }
        val dueReward = dueFulfilled.sumOf { weights.due * (0.5 + active.getValue(it).priority) }
        val violationPenalty = violated.sumOf { weights.violate * (0.5 + active.getValue(it).priority) }
        val duePenalty = dueViolated.sumOf { weights.due * (0.5 + active.getValue(it).priority) }
        val blockedPenalty = weights.blocked * blockedFulfilled.size
        val commitment = keepReward + dueReward - violationPenalty - duePenalty -
            blockedPenalty - weights.create * created.size
        val reason = when {
            effect.hard && violated.isNotEmpty() ->
                "hard commitment: ${violated.joinToString(", ")}"
            effect.hard && blockedFulfilled.isNotEmpty() ->
                "blocked hard commitment: ${blockedFulfilled.joinToString(", ")}"
            else -> null
        }
        val utilityScore = model.score(option)
        return CommitmentScore(
            utility = round6(utilityScore),
            commitment = round6(commitment),
            total = round6(utilityScore + commitment),
            fulfilled = fulfilled,
            violated = violated,
            created = created,
            dueFulfilled = dueFulfilled,
            dueViolated = dueViolated,
            blockedFulfilled = blockedFulfilled,
            blocked = reason,
        )
    }

    private fun alternatives(rows: List<Row>, bestId: String): List<Map<String, Any?>> {
        val payload = mutableListOf<Map<String, Any?>>()
        for (row in rows) {
            if (row.option.id == bestId) continue
            val reason = if (!row.feasible) {
                if (row.blocker != null) "blocked by ${row.blocker}" else "outside the hard limits"
            } else {
                "lower commitment-adjusted score"
            }
            payload += linkedMapOf(
                "action_id" to row.option.id,
                "verb" to row.option.verb.value,
                "name" to row.option.name,
                "utility" to row.score.utility,
                "commitment" to row.score.commitment,
                "total" to row.score.total,
                "rejected_because" to reason,
                "rejected_reason_code" to rejectionCode(row),
                "blocked_by" to row.blockedBy,
            )
        }
        return payload.sortedWith(compareBy({ -(it["total"] as Double) }, { it["action_id"] as String }))
    }

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

    private class Row(
        val option: ActionOption,
        val score: CommitmentScore,
        val feasible: Boolean,
        val blocker: String?,
        val blockedBy: List<Map<String, Any?>>,
    )

    private companion object {
        private val reasonPriority = listOf("missing", "stale", "unverified", "open")

        /** Map a rejected row onto a stable code for host branching. */
        fun rejectionCode(row: Row): String {
            if (row.feasible) return "lower_commitment_score"
            if (row.score.blocked?.startsWith("hard commitment") == true) {
                return "blocked_hard_commitment"
            }
            val reasons = row.blockedBy.mapNotNull { it["reason"]?.toString() }.toSet()
            for (reason in reasonPriority) {
                if (reason in reasons) return "blocked_${reason}_dependency"
            }
            return "outside_hard_limits"
        }

        fun format(pattern: String, vararg args: Any): String =
            String.format(Locale.ROOT, pattern, *args)
    }
}

internal fun commitments(problem: PlannerInput): Map<String, Commitment> {
    val attributes = problem.attributes
    val raw = attributes["commitments"] ?: attributes["commitment_ledger"] ?: return emptyMap()
    if (raw is CommitmentLedger) return raw.all().associateBy { it.id }
    val items = when (raw) {
        is Map<*, *> -> (raw["commitments"] as? List<*>) ?: emptyList()
        is Iterable<*> -> raw.toList()
        else -> emptyList()
    }
    val found = mutableListOf<Commitment>()
    for (item in items) {
        when (item) {
            is Commitment -> found += item
            is Map<*, *> -> found += Commitment.fromMap(
                item.entries.associate { it.key.toString() to it.value },
            )
        }
    }
    return found.associateBy { it.id }
}

/** Return local commitments and the graph the planner should reason over. */
internal fun activeAndGraph(problem: PlannerInput): Pair<Map<String, Commitment>, CommitmentGraph> {
    val attributes = problem.attributes
    val rawGraph = attributes["commitment_graph"]
    if (rawGraph is CommitmentGraph) {
        return rawGraph.local.all().associateBy { it.id } to rawGraph
    }
    val active = commitments(problem)
    val externalRaw = attributes["external_commitments"] ?: emptyList<Any?>()
    val externalItems = if (externalRaw is CommitmentLedger) externalRaw.all() else externalRaw
    val external = when (externalItems) {
        is Iterable<*> -> externalItems.mapNotNull { item ->
            when (item) {
                is Commitment -> item
                is Map<*, *> -> Commitment.fromMap(
                    item.entries.associate { it.key.toString() to it.value },
                )
                else -> null
            }
        }
        is Commitment -> listOf(externalItems)
        else -> emptyList()
    }
    return active to CommitmentGraph(active.values.toList(), external)
}

/** The problem's clock, falling back to now when `at` is not parseable. */
internal fun plannerNow(problem: PlannerInput): OffsetDateTime =
    parseIso(problem.at) ?: utcNow()

/** Return the graph blockers for the commitments this option fulfills. */
internal fun optionBlockers(
    option: ActionOption,
    active: Map<String, Commitment>,
    graph: CommitmentGraph,
    requireVerified: Boolean,
    now: OffsetDateTime,
    maxVerificationAge: Duration?,
): List<Map<String, Any?>> {
    val found = LinkedHashMap<Triple<String, String, String>, Map<String, Any?>>()
    for (commitmentId in commitmentEffect(option).fulfills) {
        val commitment = active[commitmentId] ?: continue
        for (blocker in graph.blockers(
            commitment,
            requireVerified = requireVerified,
            now = now,
            maxVerificationAge = maxVerificationAge,
        )) {
            found[blocker.ref.key] = blocker.toMap()
        }
    }
    return found.keys
        .sortedWith(compareBy({ it.first }, { it.second }, { it.third }))
        .map { found.getValue(it) }
}
