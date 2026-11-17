package dev.laix.decision.learning.model

import dev.laix.decision.planners.mdp.MdpModel
import dev.laix.decision.planners.mdp.MdpTransition
import dev.laix.decision.support.round
import kotlin.math.ln

/** One observed transition and its reward. */
data class Transition(
    val state: String,
    val action: String,
    val nextState: String,
    val reward: Double,
)

/** The learned distribution for one state and action. */
data class LearnedTransition(
    val state: String,
    val action: String,
    val probabilities: Map<String, Double>,
    val expectedReward: Double,
    val count: Int,
)

/**
 * A count-based transition and reward model.
 *
 * It is enough to learn a small domain model from execution outcomes, and it
 * keeps a best snapshot so a host can reject a learned model that performs
 * worse on a validation set.
 */
class ModelLearner(
    val prior: Double = 0.5,
) {
    init {
        require(prior >= 0) { "prior must not be negative" }
    }

    private val counts = LinkedHashMap<Triple<String, String, String>, Int>()
    private val rewards = LinkedHashMap<Pair<String, String>, Double>()
    private val totals = LinkedHashMap<Pair<String, String>, Int>()
    private var bestScore: Double? = null
    private var best: Map<String, Any?>? = null
    val history: MutableList<Pair<Double, Boolean>> = mutableListOf()

    /** Record one transition and its reward. */
    fun observe(state: String, action: String, nextState: String, reward: Double) {
        val key = Triple(state, action, nextState)
        counts[key] = (counts[key] ?: 0) + 1
        val pair = state to action
        rewards[pair] = (rewards[pair] ?: 0.0) + reward
        totals[pair] = (totals[pair] ?: 0) + 1
    }

    /** Return the smoothed distribution over next states. */
    fun transitionProbabilities(state: String, action: String): Map<String, Double> {
        val pair = state to action
        val total = totals[pair] ?: 0
        val outcomes = counts
            .filterKeys { it.first == state && it.second == action }
            .entries
            .associate { it.key.third to it.value }
        val denominator = total + prior * maxOf(1, outcomes.size)
        if (denominator <= 0) return emptyMap()
        return outcomes.toSortedMap().mapValues { (_, count) ->
            round((count + prior) / denominator, 6)
        }
    }

    /** Return the mean observed reward for one state and action. */
    fun expectedReward(state: String, action: String): Double {
        val pair = state to action
        val total = totals[pair] ?: 0
        if (total == 0) return 0.0
        return round((rewards[pair] ?: 0.0) / total, 6)
    }

    /** Return every learned state/action pair. */
    fun learned(): List<LearnedTransition> =
        totals.keys
            .sortedWith(compareBy({ it.first }, { it.second }))
            .map { (state, action) ->
                LearnedTransition(
                    state = state,
                    action = action,
                    probabilities = transitionProbabilities(state, action),
                    expectedReward = expectedReward(state, action),
                    count = totals.getValue(state to action),
                )
            }

    /** Turn the learned table into a finite MDP for the MDP planner. */
    fun toMdpModel(
        states: List<String>? = null,
        actions: List<String>? = null,
        start: String? = null,
        discount: Double = 0.9,
        horizon: Int? = 20,
    ): MdpModel {
        val learned = learned()
        require(learned.isNotEmpty()) { "no transitions have been learned" }
        val nextStates = learned.flatMap { it.probabilities.keys }.toSet()
        val knownStates = states ?: (
            learned.map { it.state }.toSet() + nextStates
            ).sorted()
        val knownActions = actions ?: learned.map { it.action }.toSet().sorted()
        val transitions = mutableListOf<MdpTransition>()
        for (item in learned) {
            val total = item.probabilities.values.sum()
            if (total <= 0) continue
            for ((nextState, probability) in item.probabilities) {
                if (probability <= 0) continue
                transitions += MdpTransition(
                    state = item.state,
                    action = item.action,
                    nextState = nextState,
                    probability = probability / total,
                    reward = item.expectedReward,
                )
            }
        }
        return MdpModel(
            states = knownStates,
            actions = knownActions,
            transitions = transitions,
            start = start ?: knownStates.first(),
            discount = discount,
            horizon = horizon,
        )
    }

    /**
     * Score the model on transitions it may not have seen.
     *
     * The score combines transition log-likelihood and reward error, so a
     * learned model that predicts both the next state and the reward is
     * preferred.
     */
    fun evaluate(validation: List<Transition>): Double {
        if (validation.isEmpty()) return 0.0
        val scores = validation.map { (state, action, nextState, reward) ->
            val probabilities = transitionProbabilities(state, action)
            val probability = probabilities[nextState] ?: 1e-9
            val rewardError = kotlin.math.abs(expectedReward(state, action) - reward)
            ln(probability) - rewardError
        }
        return round(scores.sum() / scores.size, 6)
    }

    /** Keep the current model only if it beats the best one so far. */
    fun commit(validation: List<Transition>): Boolean {
        val score = evaluate(validation)
        if (bestScore == null || score >= bestScore!!) {
            bestScore = score
            best = snapshot()
            history += score to true
            return true
        }
        best?.let { restore(it) }
        history += score to false
        return false
    }

    /** Return a JSON-friendly copy that can be stored or restored. */
    fun snapshot(): Map<String, Any?> =
        linkedMapOf(
            "counts" to counts.entries
                .sortedWith(compareBy({ it.key.first }, { it.key.second }, { it.key.third }))
                .map {
                    linkedMapOf(
                        "state" to it.key.first,
                        "action" to it.key.second,
                        "next_state" to it.key.third,
                        "count" to it.value,
                    )
                },
            "rewards" to rewards.entries
                .sortedWith(compareBy({ it.key.first }, { it.key.second }))
                .map {
                    linkedMapOf(
                        "state" to it.key.first,
                        "action" to it.key.second,
                        "reward" to it.value,
                    )
                },
            "totals" to totals.entries
                .sortedWith(compareBy({ it.key.first }, { it.key.second }))
                .map {
                    linkedMapOf(
                        "state" to it.key.first,
                        "action" to it.key.second,
                        "total" to it.value,
                    )
                },
        )

    /** Replace the model with a stored snapshot. */
    fun restore(snapshot: Map<String, Any?>) {
        counts.clear()
        rewards.clear()
        totals.clear()
        (snapshot["counts"] as? Iterable<*>)?.forEach { item ->
            (item as? Map<*, *>)?.let {
                val state = it["state"]?.toString() ?: ""
                val action = it["action"]?.toString() ?: ""
                val nextState = it["next_state"]?.toString() ?: ""
                counts[Triple(state, action, nextState)] = (it["count"] as? Number)?.toInt() ?: 0
            }
        }
        (snapshot["rewards"] as? Iterable<*>)?.forEach { item ->
            (item as? Map<*, *>)?.let {
                val state = it["state"]?.toString() ?: ""
                val action = it["action"]?.toString() ?: ""
                rewards[state to action] = (it["reward"] as? Number)?.toDouble() ?: 0.0
            }
        }
        (snapshot["totals"] as? Iterable<*>)?.forEach { item ->
            (item as? Map<*, *>)?.let {
                val state = it["state"]?.toString() ?: ""
                val action = it["action"]?.toString() ?: ""
                totals[state to action] = (it["total"] as? Number)?.toInt() ?: 0
            }
        }
    }

    fun bestScore(): Double? = bestScore
}
