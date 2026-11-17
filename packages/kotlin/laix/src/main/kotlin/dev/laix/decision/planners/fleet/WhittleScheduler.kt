package dev.laix.decision.planners.fleet

import dev.laix.decision.support.round6
import kotlin.math.abs

/** One transition for the active or passive action. */
data class WhittleTransition(
    val state: String,
    val nextState: String,
    val probability: Double = 1.0,
)

/** A two-action restless arm: review (active) or defer (passive). */
data class WhittleCandidate(
    val id: String,
    val states: List<String>,
    val start: String,
    val activeTransitions: List<WhittleTransition>,
    val passiveTransitions: List<WhittleTransition>,
    val activeReward: Map<String, Double> = emptyMap(),
    val passiveReward: Map<String, Double> = emptyMap(),
    val activeCost: Double = 0.0,
    val reviewCost: Double = 1.0,
    val discount: Double = 0.9,
)

/** The index and allocation for one candidate. */
data class WhittleRow(
    val candidateId: String,
    val index: Double,
    val selected: Boolean,
    val reviewCost: Double,
    val reason: String,
)

/** The ordered Whittle schedule. */
data class WhittleSchedule(
    val budget: Double,
    val spent: Double,
    val rows: List<WhittleRow>,
    val selected: List<WhittleRow>,
    val deferred: List<WhittleRow>,
)

private fun rows(
    transitions: List<WhittleTransition>,
    state: String,
): List<WhittleTransition> = transitions.filter { it.state == state }

private fun validate(candidate: WhittleCandidate) {
    require(candidate.states.isNotEmpty()) { "a Whittle candidate needs at least one state" }
    require(candidate.start in candidate.states) { "unknown start state: '${candidate.start}'" }
    require(candidate.discount in 0.0..1.0) { "discount must be between zero and one" }
    for (transitions in listOf(candidate.activeTransitions, candidate.passiveTransitions)) {
        for (item in transitions) {
            require(item.state in candidate.states && item.nextState in candidate.states) {
                "transition refers to an unknown state: $item"
            }
            require(item.probability in 0.0..1.0) {
                "transition probability must be between zero and one"
            }
        }
        for (state in candidate.states) {
            val values = rows(transitions, state)
            if (values.isNotEmpty()) {
                require(abs(values.sumOf { it.probability } - 1.0) <= 1e-6) {
                    "transitions for '$state' do not sum to one"
                }
            }
        }
    }
}

private fun expectation(
    transitions: List<WhittleTransition>,
    state: String,
    values: Map<String, Double>,
): Double =
    rows(transitions, state).sumOf {
        it.probability * (values[it.nextState] ?: 0.0)
    }

/** Value iteration for the single arm with a passive subsidy. */
private fun values(candidate: WhittleCandidate, subsidy: Double): Map<String, Double> {
    var current = candidate.states.associateWith { 0.0 }
    repeat(1000) {
        val updated = LinkedHashMap<String, Double>()
        for (state in candidate.states) {
            val active = (candidate.activeReward[state] ?: 0.0) -
                candidate.activeCost +
                candidate.discount * expectation(candidate.activeTransitions, state, current)
            val passive = (candidate.passiveReward[state] ?: 0.0) +
                subsidy +
                candidate.discount * expectation(candidate.passiveTransitions, state, current)
            updated[state] = maxOf(active, passive)
        }
        if (candidate.states.maxOf { abs(updated.getValue(it) - current.getValue(it)) } < 1e-9) {
            return updated
        }
        current = updated
    }
    return current
}

private fun passiveIsBetter(candidate: WhittleCandidate, subsidy: Double): Boolean {
    val solved = values(candidate, subsidy)
    val state = candidate.start
    val active = (candidate.activeReward[state] ?: 0.0) -
        candidate.activeCost +
        candidate.discount * expectation(candidate.activeTransitions, state, solved)
    val passive = (candidate.passiveReward[state] ?: 0.0) +
        subsidy +
        candidate.discount * expectation(candidate.passiveTransitions, state, solved)
    return passive >= active
}

/** Return the subsidy where passive becomes at least as good as active. */
fun whittleIndex(
    candidate: WhittleCandidate,
    lower: Double = -10.0,
    upper: Double = 10.0,
    iterations: Int = 60,
): Double {
    validate(candidate)
    if (passiveIsBetter(candidate, lower)) return round6(lower)
    if (!passiveIsBetter(candidate, upper)) return round6(upper)
    var low = lower
    var high = upper
    repeat(maxOf(1, iterations)) {
        val mid = (low + high) / 2
        if (passiveIsBetter(candidate, mid)) high = mid else low = mid
    }
    return round6((low + high) / 2)
}

/** Rank candidates by their exact Whittle index and allocate attention. */
class WhittleScheduler(
    val lower: Double = -10.0,
    val upper: Double = 10.0,
    val iterations: Int = 60,
) {
    val name: String = "aads.whittle.v1"

    fun schedule(
        candidates: List<WhittleCandidate>,
        budget: Double = 1.0,
    ): WhittleSchedule {
        val limit = maxOf(0.0, budget)
        val ranked = candidates
            .map { it to whittleIndex(it, lower, upper, iterations) }
            .sortedWith(compareBy({ -it.second }, { it.first.id }))
        var spent = 0.0
        val rows = ranked.map { (candidate, index) ->
            val reviewCost = maxOf(1e-9, candidate.reviewCost)
            val selected = spent + reviewCost <= limit + 1e-9
            if (selected) spent += reviewCost
            WhittleRow(
                candidateId = candidate.id,
                index = index,
                selected = selected,
                reviewCost = round6(reviewCost),
                reason = if (selected) "within attention budget" else "attention budget exhausted",
            )
        }
        return WhittleSchedule(
            budget = round6(limit),
            spent = round6(spent),
            rows = rows,
            selected = rows.filter { it.selected },
            deferred = rows.filter { !it.selected },
        )
    }
}
