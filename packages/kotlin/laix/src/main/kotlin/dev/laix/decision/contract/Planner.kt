package dev.laix.decision.contract

import dev.laix.decision.contracts.ActionOption
import dev.laix.decision.contracts.Situation
import dev.laix.decision.contracts.Verb

data class PlannerInput(
    val subject: String,
    val at: String,
    val situation: Situation? = null,
    val options: List<ActionOption> = emptyList(),
    val signals: List<Any?> = emptyList(),
    val context: Any? = null,
    val attributes: Map<String, Any?> = emptyMap(),
)

data class PlannerResult(
    val verb: Verb,
    val confidence: Double,
    val reasonCode: String,
    val rationale: String,
    val actionId: String? = null,
    val requiresApproval: Boolean = false,
    val reversible: Boolean = false,
    val score: Double? = null,
    val alternatives: List<Map<String, Any?>> = emptyList(),
    val attributes: Map<String, Any?> = emptyMap(),
)

fun interface Planner {
    fun solve(problem: PlannerInput): PlannerResult
}
