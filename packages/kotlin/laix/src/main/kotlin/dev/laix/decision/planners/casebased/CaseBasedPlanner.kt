package dev.laix.decision.planners.casebased

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.round6

/** One observed subject, action and outcome. */
data class PastDecision(
    val subject: String,
    val actionId: String,
    val verb: Verb = Verb.ACT,
    val attributes: Map<String, Any?> = emptyMap(),
)

/** Choose the action from the most similar past decision. */
class CaseBasedPlanner(
    cases: List<PastDecision>,
    private val fallback: Planner? = null,
    val threshold: Double = 0.2,
) : Planner {
    init {
        require(threshold in 0.0..1.0) { "threshold must be between zero and one" }
    }

    val name: String = "case_based.v1"

    val cases: List<PastDecision> = cases.toList()

    override fun solve(problem: PlannerInput): PlannerResult {
        val scored = cases
            .map { similarity(problem, it) to it }
            .sortedWith(
                compareBy(
                    { -it.first },
                    { it.second.subject },
                    { it.second.actionId },
                ),
            )
        val best = scored.firstOrNull()
        if (best != null && best.first >= threshold) {
            val (similarity, case) = best
            return PlannerResult(
                verb = case.verb,
                confidence = similarity,
                reasonCode = "case_based",
                rationale = "${case.subject} is the closest past decision",
                actionId = case.actionId,
                attributes = linkedMapOf<String, Any?>(
                    "case_subject" to case.subject,
                    "case_similarity" to similarity,
                ) + case.attributes,
            )
        }
        if (fallback != null) return fallback.solve(problem)
        return PlannerResult(
            verb = Verb.WAIT,
            confidence = 1.0,
            reasonCode = "no_case",
            rationale = "no similar past decision",
            score = 0.0,
        )
    }

    private fun similarity(problem: PlannerInput, case: PastDecision): Double {
        val wanted = tokens(problem.subject)
        val found = tokens(case.subject)
        val token = if (wanted.isNotEmpty() && found.isNotEmpty()) {
            wanted.intersect(found).size.toDouble() / wanted.union(found).size
        } else {
            0.0
        }
        val action = if (problem.options.any { it.id == case.actionId }) 1.0 else 0.0
        return round6(0.7 * token + 0.3 * action)
    }

    private fun tokens(value: String): Set<String> =
        Regex("[a-z0-9]+").findAll(value.lowercase()).map { it.value }.toSet()
}
