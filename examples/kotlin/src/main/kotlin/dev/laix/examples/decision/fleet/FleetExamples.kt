package dev.laix.examples.decision.fleet

import dev.laix.decision.planners.fleet.AttentionCandidate
import dev.laix.decision.planners.fleet.AttentionScheduler
import dev.laix.decision.planners.fleet.WhittleCandidate
import dev.laix.decision.planners.fleet.WhittleScheduler
import dev.laix.decision.planners.fleet.WhittleTransition
import dev.laix.examples.AT

/** Rank a fleet by expected gain per review minute. */
fun attentionScheduler(): String {
    val schedule = AttentionScheduler().schedule(
        candidates = listOf(
            AttentionCandidate("risk", risk = 0.8, value = 0.9, reviewCost = 0.5),
            AttentionCandidate("noise", risk = 0.1, value = 0.1, reviewCost = 1.5),
        ),
        now = AT,
        budget = 1.0,
    )
    return "selected=${schedule.selected.map { it.candidateId }} spent=${schedule.spent}"
}

/** Rank the same fleet by its Whittle index. */
fun whittleScheduler(): String {
    val states = listOf("healthy", "degraded")
    fun candidate(id: String, start: String) = WhittleCandidate(
        id = id,
        states = states,
        start = start,
        activeTransitions = listOf(
            WhittleTransition("degraded", "healthy", 0.8),
            WhittleTransition("degraded", "degraded", 0.2),
            WhittleTransition("healthy", "healthy", 1.0),
        ),
        passiveTransitions = listOf(
            WhittleTransition("healthy", "degraded", 0.3),
            WhittleTransition("healthy", "healthy", 0.7),
            WhittleTransition("degraded", "degraded", 1.0),
        ),
        activeReward = mapOf("healthy" to 1.0, "degraded" to 0.2),
        passiveReward = mapOf("healthy" to 0.4, "degraded" to 0.0),
        activeCost = 0.1,
        reviewCost = 0.5,
    )
    val schedule = WhittleScheduler().schedule(
        candidates = listOf(candidate("pump", "degraded"), candidate("valve", "healthy")),
        budget = 1.0,
    )
    return "selected=${schedule.selected.map { it.candidateId }} spent=${schedule.spent}"
}
