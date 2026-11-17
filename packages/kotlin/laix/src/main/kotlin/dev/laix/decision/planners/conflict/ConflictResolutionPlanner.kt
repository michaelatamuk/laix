package dev.laix.decision.planners.conflict

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Verb

/** Choose a conflict response, or delegate when there is no conflict. */
class ConflictResolutionPlanner(
    private val planner: Planner? = null,
    val severityLimit: Double = 0.5,
    val escalateAt: Double = 0.8,
) : Planner {
    init {
        require(severityLimit in 0.0..1.0) { "severity_limit must be between zero and one" }
        require(escalateAt in 0.0..1.0) { "escalate_at must be between zero and one" }
    }

    val name: String = "conflict_resolution.v1"

    override fun solve(problem: PlannerInput): PlannerResult {
        val raw = problem.attributes["goal_conflicts"] as? Iterable<*> ?: emptyList<Any?>()
        val conflicts = raw
            .filterIsInstance<Map<*, *>>()
            .map { it.entries.associate { entry -> entry.key.toString() to entry.value } }
            .filter { severity(it) >= severityLimit }

        if (conflicts.isEmpty()) {
            if (planner != null) return planner.solve(problem)
            return PlannerResult(
                verb = Verb.WAIT,
                confidence = 1.0,
                reasonCode = "no_goal_conflict",
                rationale = "no goal conflict needs resolution",
                score = 0.0,
            )
        }

        val wanted = conflicts.map { conflictId(it) }.toSet()
        for (option in problem.options) {
            val resolves = (option.params["resolves"] as? Iterable<*>)
                ?.map { it.toString() }
                ?.toSet()
                ?: emptySet()
            if (resolves.containsAll(wanted)) {
                return PlannerResult(
                    verb = option.verb,
                    confidence = 0.8,
                    reasonCode = "goal_conflict_resolved",
                    rationale = "${option.id} resolves the active goal conflicts",
                    actionId = option.id,
                    attributes = mapOf("goal_conflicts" to conflicts),
                )
            }
        }

        val escalate = conflicts.any { severity(it) >= escalateAt }
        return PlannerResult(
            verb = if (escalate) Verb.ESCALATE else Verb.ASK,
            confidence = 0.8,
            reasonCode = if (escalate) "goal_conflict" else "goal_conflict_needs_choice",
            rationale = "${conflicts.size} goal conflicts need a decision",
            attributes = mapOf("goal_conflicts" to conflicts),
        )
    }

    private fun severity(conflict: Map<String, Any?>): Double =
        when (val value = conflict["severity"]) {
            is Number -> value.toDouble()
            is String -> value.toDoubleOrNull() ?: 0.0
            else -> 0.0
        }

    private fun conflictId(conflict: Map<String, Any?>): String =
        conflict["id"]?.toString() ?: "${conflict["left"]}:${conflict["right"]}"
}
