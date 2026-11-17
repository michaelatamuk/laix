package dev.laix.decision.planners.history

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.Verb

/** Re-run a planner and decide `hold`, `revise` or `escalate`. */
class RevalidationPlanner(
    private val planner: Planner,
    val escalateOnInfeasible: Boolean = true,
) : Planner {
    val name: String = "revalidation.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        val previous = previousAction(problem)
        val current = planner.solve(problem)

        if (previous == null) {
            return current.copy(
                reasonCode = "revalidated_new",
                attributes = current.attributes + mapOf(
                    "previous_action_id" to null,
                    "current_action_id" to current.actionId,
                ),
            )
        }

        if (current.actionId == previous) {
            return PlannerResult(
                verb = Verb.WAIT,
                confidence = current.confidence,
                reasonCode = "decision_held",
                rationale = "$previous is still the best action",
                actionId = previous,
                score = current.score,
                attributes = current.attributes + mapOf(
                    "previous_action_id" to previous,
                    "current_action_id" to current.actionId,
                    "held" to true,
                ),
            )
        }

        if (escalateOnInfeasible &&
            current.reasonCode in setOf("no_feasible_option", "no_options")
        ) {
            return PlannerResult(
                verb = Verb.ESCALATE,
                confidence = 1.0,
                reasonCode = "decision_escalated",
                rationale = "$previous is no longer feasible",
                actionId = previous,
                attributes = current.attributes + mapOf(
                    "previous_action_id" to previous,
                    "current_action_id" to current.actionId,
                    "escalated" to true,
                ),
            )
        }

        return current.copy(
            reasonCode = "decision_revised",
            attributes = current.attributes + mapOf(
                "previous_action_id" to previous,
                "current_action_id" to current.actionId,
            ),
        )
    }

    private fun previousAction(problem: PlannerInput): String? {
        val attributes = problem.attributes
        val raw = attributes["previous_decision"] ?: attributes["previous"]
        return when (raw) {
            is PlannerResult -> raw.actionId
            is Decision -> raw.actionId
            is Map<*, *> -> (raw["action_id"] ?: raw["actionId"])?.toString()
            else -> attributes["previous_action_id"]?.toString()
        }
    }
}
