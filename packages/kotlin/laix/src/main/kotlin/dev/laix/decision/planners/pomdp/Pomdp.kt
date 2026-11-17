package dev.laix.decision.planners.pomdp

import dev.laix.decision.contract.Planner
import dev.laix.decision.contract.PlannerInput
import dev.laix.decision.contract.PlannerResult
import dev.laix.decision.contracts.Verb
import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.valueIteration
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round
import java.util.Locale
import kotlin.math.abs
import kotlin.math.log2

/** One transition in the hidden state. */
data class PomdpTransition(
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

/** The chance of an observation after an action and a hidden state. */
data class ObservationProbability(
    val nextState: String,
    val action: String,
    val observation: String,
    val probability: Double = 1.0,
) {
    init {
        require(probability in 0.0..1.0) {
            "observation probability must be between zero and one"
        }
    }
}

/** A finite POMDP with discrete states, actions and observations. */
data class PomdpModel(
    val states: List<String>,
    val actions: List<String>,
    val observations: List<String>,
    val transitions: List<PomdpTransition>,
    val observationTable: List<ObservationProbability>,
    val discount: Double = 0.9,
    val horizon: Int = 3,
) {
    init {
        require(states.isNotEmpty()) { "a POMDP needs at least one state" }
        require(actions.isNotEmpty()) { "a POMDP needs at least one action" }
        require(observations.isNotEmpty()) { "a POMDP needs at least one observation" }
        require(states.size == states.toSet().size) { "POMDP states must be unique" }
        require(actions.size == actions.toSet().size) { "POMDP actions must be unique" }
        require(observations.size == observations.toSet().size) {
            "POMDP observations must be unique"
        }
        require(discount in 0.0..1.0) { "discount must be between zero and one" }
        require(horizon >= 0) { "horizon must not be negative" }
        val knownStates = states.toSet()
        val knownActions = actions.toSet()
        val knownObservations = observations.toSet()
        for (item in transitions) {
            require(item.state in knownStates && item.nextState in knownStates) {
                "transition refers to an unknown state: $item"
            }
            require(item.action in knownActions) {
                "transition refers to an unknown action: $item"
            }
        }
        for (item in observationTable) {
            require(item.nextState in knownStates) {
                "observation refers to an unknown state: $item"
            }
            require(item.action in knownActions) {
                "observation refers to an unknown action: $item"
            }
            require(item.observation in knownObservations) { "unknown observation: $item" }
        }

        for (state in states) {
            for (action in actions) {
                val rows = transitionRows(state, action)
                if (rows.isNotEmpty()) {
                    val total = rows.sumOf { it.probability }
                    require(abs(total - 1.0) <= 1e-6) {
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
        val reachable = transitions
            .filter { it.probability > 0 }
            .map { it.nextState to it.action }
            .distinct()
            .sortedWith(compareBy({ it.first }, { it.second }))
        for ((nextState, action) in reachable) {
            val rows = observationRows(nextState, action)
            require(rows.isNotEmpty()) {
                "missing observations for '$nextState'/'$action'"
            }
            val total = rows.sumOf { it.probability }
            require(abs(total - 1.0) <= 1e-6) {
                String.format(
                    Locale.ROOT,
                    "observations for '%s'/'%s' sum to %.6f",
                    nextState,
                    action,
                    total,
                )
            }
        }
    }

    fun transitionRows(state: String, action: String): List<PomdpTransition> =
        transitions.filter { it.state == state && it.action == action }

    fun observationRows(nextState: String, action: String): List<ObservationProbability> =
        observationTable.filter { it.nextState == nextState && it.action == action }

    fun actionAvailable(state: String, action: String): Boolean =
        transitionRows(state, action).isNotEmpty()
}

/** A sanity check between a POMDP belief and its most likely MDP state. */
data class PlannerComparison(
    val pomdp: Double,
    val mdp: Double,
    val gap: Double,
    val state: String,
)

/** Clamp, drop unknowns and renormalise one belief. */
fun normalizeBelief(belief: Map<String, Double>, states: Collection<String>): Map<String, Double> {
    val allowed = states.toSet()
    val clean = LinkedHashMap<String, Double>()
    for ((state, probability) in belief) {
        if (state in allowed) clean[state] = maxOf(0.0, probability)
    }
    val total = clean.values.sum()
    if (total <= 0) {
        val size = maxOf(1, allowed.size)
        return allowed.associateWith { 1.0 / size }
    }
    return clean.mapValues { (_, probability) -> round(probability / total, 9) }
}

/** Put all belief on one state. */
fun beliefFromState(state: String, states: Collection<String>): Map<String, Double> {
    require(state in states) { "unknown state: '$state'" }
    return states.associateWith { if (it == state) 1.0 else 0.0 }
}

/** Bayes update after one action and one observation. */
fun beliefUpdate(
    model: PomdpModel,
    belief: Map<String, Double>,
    action: String,
    observation: String,
): Map<String, Double> {
    val current = normalizeBelief(belief, model.states)
    val predicted = LinkedHashMap<String, Double>()
    for (nextState in model.states) {
        val probability = model.states.sumOf { state ->
            (current[state] ?: 0.0) *
                model.transitionRows(state, action)
                    .filter { it.nextState == nextState }
                    .sumOf { it.probability }
        }
        if (probability != 0.0) predicted[nextState] = probability
    }
    if (predicted.isEmpty()) return current

    val likelihood = predicted.keys.associateWith { nextState ->
        model.observationRows(nextState, action)
            .firstOrNull { it.observation == observation }
            ?.probability ?: 0.0
    }
    val unnormalised = predicted.mapValues { (nextState, probability) ->
        probability * likelihood.getValue(nextState)
    }
    val total = unnormalised.values.sum()
    if (total <= 0) return normalizeBelief(predicted, model.states)
    return unnormalised.mapValues { (_, probability) -> round(probability / total, 9) }
}

/** P(observation | belief, action). */
fun observationProbability(
    model: PomdpModel,
    belief: Map<String, Double>,
    action: String,
    observation: String,
): Double {
    val current = normalizeBelief(belief, model.states)
    var total = 0.0
    for (nextState in model.states) {
        val transition = model.states.sumOf { state ->
            (current[state] ?: 0.0) *
                model.transitionRows(state, action)
                    .filter { it.nextState == nextState }
                    .sumOf { it.probability }
        }
        val chance = model.observationRows(nextState, action)
            .firstOrNull { it.observation == observation }
            ?.probability ?: 0.0
        total += transition * chance
    }
    return total
}

/** Shannon entropy, in bits, of one belief. */
fun beliefEntropy(belief: Map<String, Double>): Double {
    val total = belief.values.sum()
    if (total <= 0) return 0.0
    var entropy = 0.0
    for (probability in belief.values) {
        val value = probability / total
        if (value > 0) entropy -= value * log2(value)
    }
    return round(entropy, 6)
}

private fun immediateReward(
    model: PomdpModel,
    belief: Map<String, Double>,
    action: String,
): Double =
    model.states.sumOf { state ->
        model.transitionRows(state, action).sumOf {
            (belief[state] ?: 0.0) * it.probability * it.reward
        }
    }

private class Evaluator(private val model: PomdpModel) {
    private val cache =
        HashMap<Triple<List<Pair<String, Double>>, String, Int>, Double>()

    fun actionValue(
        belief: Map<String, Double>,
        action: String,
        depth: Int,
    ): Double {
        val key = Triple(belief.entries.map { it.key to it.value }.sortedBy { it.first }, action, depth)
        cache[key]?.let { return it }
        var value = immediateReward(model, belief, action)
        if (depth > 0) {
            var future = 0.0
            for (observation in model.observations) {
                val chance = observationProbability(model, belief, action, observation)
                if (chance <= 0) continue
                val updated = beliefUpdate(model, belief, action, observation)
                future += chance * bestValue(updated, depth - 1)
            }
            value += model.discount * future
        }
        cache[key] = value
        return value
    }

    fun bestValue(belief: Map<String, Double>, depth: Int): Double {
        if (depth < 0) return 0.0
        val actions = model.actions.filter { action ->
            belief.keys.any { model.actionAvailable(it, action) }
        }
        if (actions.isEmpty()) return 0.0
        return actions.maxOf { actionValue(belief, it, depth) }
    }
}

/** Best expected value of a belief over a finite horizon. */
fun pomdpValue(
    model: PomdpModel,
    belief: Map<String, Double>,
    horizon: Int? = null,
): Double {
    val resolved = normalizeBelief(belief, model.states)
    val steps = horizon ?: model.horizon
    if (steps <= 0) return 0.0
    return round(Evaluator(model).bestValue(resolved, steps - 1), 6)
}

/**
 * Discounted future value of one action under a belief.
 *
 * The immediate reward is excluded. This is the no-double-count building
 * block for planners that already carry their own immediate score.
 */
fun actionFutureValue(
    model: PomdpModel,
    belief: Map<String, Double>,
    action: String,
    horizon: Int? = null,
): Double {
    val resolved = normalizeBelief(belief, model.states)
    val steps = horizon ?: model.horizon
    if (steps <= 1) return 0.0
    var future = 0.0
    for (observation in model.observations) {
        val chance = observationProbability(model, resolved, action, observation)
        if (chance <= 0) continue
        val updated = beliefUpdate(model, resolved, action, observation)
        future += chance * Evaluator(model).bestValue(updated, steps - 2)
    }
    return round(model.discount * future, 6)
}

/**
 * Compare the belief value with the MDP value of the most likely state.
 *
 * This is a diagnostic, not an optimality proof: a POMDP can be worth less
 * than the fully observable MDP because uncertainty is real.
 */
fun comparePomdpToMdp(
    pomdp: PomdpModel,
    mdp: MdpModel,
    belief: Map<String, Double>,
    horizon: Int? = null,
): PlannerComparison {
    val resolved = normalizeBelief(belief, pomdp.states)
    val state = resolved.entries
        .maxWith(compareBy({ it.value }, { it.key }))
        .key
    val pomdpScore = pomdpValue(pomdp, resolved, horizon)
    val mdpScore = round(valueIteration(mdp).getValue(state), 6)
    return PlannerComparison(
        pomdp = pomdpScore,
        mdp = mdpScore,
        gap = round(abs(pomdpScore - mdpScore), 6),
        state = state,
    )
}

/** Choose the action with the highest belief-state value. */
class POMDPPlanner(
    val model: PomdpModel,
    val belief: Map<String, Double> = emptyMap(),
) : Planner {
    val name: String = "pomdp.v1"
    val version: String = name

    override fun solve(problem: PlannerInput): PlannerResult {
        val attributes = problem.attributes
        val resolved = resolveBelief(attributes)
        val horizon = (attributes["horizon"] as? Number)?.toInt() ?: model.horizon
        val depth = maxOf(-1, horizon - 1)
        val evaluator = Evaluator(model)
        val rows = model.actions
            .filter { action -> resolved.keys.any { model.actionAvailable(it, action) } }
            .map { action -> action to round(evaluator.actionValue(resolved, action, depth), 6) }
            .sortedWith(compareBy({ -it.second }, { it.first }))

        if (rows.isEmpty()) {
            return PlannerResult(
                verb = Verb.WAIT,
                confidence = 1.0,
                reasonCode = "no_action",
                rationale = "no action is available under the current belief",
                score = 0.0,
            )
        }

        val (bestAction, bestValue) = rows.first()
        val second = rows.getOrNull(1)?.second
        return PlannerResult(
            verb = Verb.ACT,
            confidence = confidence(bestValue, second),
            reasonCode = "pomdp_plan",
            rationale = String.format(
                Locale.ROOT,
                "%s has the highest expected value %.3f under the current belief",
                bestAction,
                bestValue,
            ),
            actionId = bestAction,
            score = bestValue,
            alternatives = rows.drop(1).map { (action, value) ->
                linkedMapOf(
                    "action_id" to action,
                    "value" to value,
                    "rejected_because" to "lower expected value",
                )
            },
            attributes = linkedMapOf(
                "belief" to resolved,
                "entropy" to beliefEntropy(resolved),
                "horizon" to horizon,
            ),
        )
    }

    private fun resolveBelief(attributes: Map<String, Any?>): Map<String, Double> {
        val value = attributes["belief"]
        if (value is Map<*, *>) {
            return normalizeBelief(numberMap(value), model.states)
        }
        if (belief.isNotEmpty()) return normalizeBelief(belief, model.states)
        val state = attributes["state"] as? String
        if (!state.isNullOrEmpty()) return beliefFromState(state, model.states)
        val size = model.states.size
        return model.states.associateWith { 1.0 / size }
    }

    private fun numberMap(value: Map<*, *>): Map<String, Double> {
        val result = LinkedHashMap<String, Double>()
        for ((key, item) in value) {
            val numeric = when (item) {
                is Number -> item.toDouble()
                is String -> item.toDoubleOrNull()
                else -> null
            }
            if (numeric != null) result[key.toString()] = numeric
        }
        return result
    }

    private fun confidence(best: Double, second: Double?): Double {
        if (second == null) return 1.0
        val gap = maxOf(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / maxOf(abs(best), 1e-9)))
    }
}
