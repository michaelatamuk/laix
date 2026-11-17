package dev.laix.decision.planners.mdp

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Verb
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round6
import java.util.Locale

/** One probabilistic transition from a state under an action. */
data class MdpTransition(
    val state: String,
    val action: String,
    val nextState: String,
    val probability: Double = 1.0,
    val reward: Double = 0.0,
) {
    init {
        require(probability in 0.0..1.0) {
            "transition probability must be between zero and one"
        }
    }
}

/** A finite, discrete MDP. */
data class MdpModel(
    val states: List<String>,
    val actions: List<String>,
    val transitions: List<MdpTransition>,
    val start: String,
    val discount: Double = 0.9,
    val horizon: Int? = 20,
) {
    init {
        require(states.isNotEmpty()) { "an MDP needs at least one state" }
        require(states.size == states.toSet().size) { "MDP states must be unique" }
        require(actions.size == actions.toSet().size) { "MDP actions must be unique" }
        require(start in states) { "unknown start state: '$start'" }
        require(discount in 0.0..1.0) { "discount must be between zero and one" }
        require(horizon == null || horizon >= 0) { "horizon must not be negative" }
        val knownStates = states.toSet()
        val knownActions = actions.toSet()
        for (item in transitions) {
            require(item.state in knownStates && item.nextState in knownStates) {
                "transition refers to an unknown state: $item"
            }
            require(item.action in knownActions) {
                "transition refers to an unknown action: $item"
            }
        }
        for (state in states) {
            for (action in actions) {
                val rows = outgoing(state, action)
                if (rows.isNotEmpty()) {
                    val total = rows.sumOf { it.probability }
                    require(kotlin.math.abs(total - 1.0) <= 1e-6) {
                        String.format(
                            Locale.ROOT,
                            "transitions for '%s'/'%s' sum to %.6f",
                            state,
                            action,
                            total,
                        )
                    }
                }
            }
        }
    }

    fun outgoing(state: String, action: String): List<MdpTransition> =
        transitions.filter { it.state == state && it.action == action }

    fun actionsFor(state: String): List<String> =
        actions.filter { outgoing(state, it).isNotEmpty() }
}

/** A stationary policy and its state values. */
data class PolicyIterationResult(
    val policy: Map<String, String>,
    val values: Map<String, Double>,
    val iterations: Int,
)

private fun qValue(
    model: MdpModel,
    state: String,
    action: String,
    values: Map<String, Double>,
): Double =
    model.outgoing(state, action).sumOf {
        it.probability * (it.reward + model.discount * values.getValue(it.nextState))
    }

/**
 * Return the value of every state under a finite or infinite horizon.
 *
 * [horizon] overrides the model's horizon. A horizon of zero means no
 * lookahead: every state is worth zero.
 */
fun valueIteration(
    model: MdpModel,
    horizon: Int? = null,
    tolerance: Double = 1e-9,
    maxIterations: Int = 1000,
): Map<String, Double> {
    var values = model.states.associateWith { 0.0 }
    val limit = horizon ?: model.horizon
    if (limit != null && limit <= 0) return values
    val iterations = limit ?: maxIterations
    repeat(iterations) {
        val updated = LinkedHashMap<String, Double>()
        var delta = 0.0
        for (state in model.states) {
            val actions = model.actionsFor(state)
            if (actions.isEmpty()) {
                updated[state] = 0.0
                continue
            }
            val value = actions.maxOf { qValue(model, state, it, values) }
            updated[state] = value
            delta = maxOf(delta, kotlin.math.abs(value - values.getValue(state)))
        }
        values = updated
        if (delta <= tolerance) return values
    }
    return values
}

/** Solve a discounted infinite-horizon MDP with policy iteration. */
fun policyIteration(
    model: MdpModel,
    tolerance: Double = 1e-9,
    maxIterations: Int = 1000,
): PolicyIterationResult {
    require(model.horizon == null) { "policy iteration needs an infinite horizon" }
    val policy = LinkedHashMap<String, String>()
    for (state in model.states) {
        model.actionsFor(state).firstOrNull()?.let { policy[state] = it }
    }
    var values = model.states.associateWith { 0.0 }

    for (iteration in 1..maxIterations) {
        var converged = false
        var inner = 0
        while (inner < maxIterations && !converged) {
            val updated = LinkedHashMap<String, Double>()
            var delta = 0.0
            for (state in model.states) {
                val action = policy[state]
                val value = if (action == null) 0.0 else qValue(model, state, action, values)
                updated[state] = value
                delta = maxOf(delta, kotlin.math.abs(value - values.getValue(state)))
            }
            values = updated
            if (delta <= tolerance) converged = true
            inner++
        }

        var changed = false
        for (state in model.states) {
            val actions = model.actionsFor(state)
            if (actions.isEmpty()) continue
            val best = actions.maxByOrNull { qValue(model, state, it, values) }
            if (best != null && policy[state] != best) {
                policy[state] = best
                changed = true
            }
        }
        if (!changed) {
            return PolicyIterationResult(
                policy = policy.toMap(),
                values = values.toMap(),
                iterations = iteration,
            )
        }
    }

    return PolicyIterationResult(
        policy = policy.toMap(),
        values = values.toMap(),
        iterations = maxIterations,
    )
}

/** Values of the states reached after the first action. */
private fun lookaheadValues(model: MdpModel): Map<String, Double> =
    if (model.horizon == null) {
        valueIteration(model)
    } else {
        valueIteration(model, horizon = maxOf(-1, model.horizon - 1))
    }

/** Return `(action, expected value)` in descending value order. */
fun actionValues(
    model: MdpModel,
    state: String,
    values: Map<String, Double>? = null,
): List<Pair<String, Double>> {
    val resolved = values ?: lookaheadValues(model)
    return model.actionsFor(state)
        .map { action -> action to round6(qValue(model, state, action, resolved)) }
        .sortedWith(compareBy({ -it.second }, { it.first }))
}

/** Choose the action with the highest value in a finite MDP. */
class MDPPlanner(
    val model: MdpModel,
    val state: String = model.start,
) : Planner {
    val name: String = "mdp.v1"
    val version: String = name

    override fun solve(problem: PlannerInput): PlannerResult {
        val current = problem.attributes["state"]?.toString() ?: state
        require(current in model.states) { "unknown state: '$current'" }
        val rows = actionValues(model, current)
        if (rows.isEmpty()) {
            return PlannerResult(
                verb = Verb.WAIT,
                confidence = 1.0,
                reasonCode = "terminal_state",
                rationale = "$current has no action to take",
                score = 0.0,
                attributes = mapOf("state" to current),
            )
        }

        val (bestAction, bestValue) = rows.first()
        val second = rows.getOrNull(1)?.second
        val alternatives = rows.drop(1).map { (action, value) ->
            linkedMapOf(
                "action_id" to action,
                "value" to value,
                "rejected_because" to "lower expected value",
            )
        }

        return PlannerResult(
            verb = Verb.ACT,
            confidence = confidence(bestValue, second),
            reasonCode = "mdp_plan",
            rationale = String.format(
                Locale.ROOT,
                "%s has the highest expected value %.3f from %s",
                bestAction,
                bestValue,
                current,
            ),
            actionId = bestAction,
            score = bestValue,
            alternatives = alternatives,
            attributes = linkedMapOf(
                "state" to current,
                "expected_value" to bestValue,
                "discount" to model.discount,
                "horizon" to model.horizon,
            ),
        )
    }

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(kotlin.math.abs(best), 1e-9)))
    }
}

/** Return the greedy action sequence for one state. */
fun planActions(
    model: MdpModel,
    state: String? = null,
): List<String> {
    var current = state ?: model.start
    val path = mutableListOf<String>()
    val seen = mutableSetOf<String>()
    while (current !in seen) {
        seen += current
        val rows = actionValues(model, current)
        if (rows.isEmpty()) break
        val action = rows.first().first
        path += "$current:$action"
        val outcomes = model.outgoing(current, action)
        if (outcomes.isEmpty()) break
        current = outcomes
            .sortedWith(compareBy({ -it.probability }, { it.nextState }))
            .first()
            .nextState
    }
    return path
}
