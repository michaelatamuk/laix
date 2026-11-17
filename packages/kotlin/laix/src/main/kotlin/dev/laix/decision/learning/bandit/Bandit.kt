package dev.laix.decision.learning.bandit

import dev.laix.decision.outcomes.Outcome
import dev.laix.decision.support.clamp
import dev.laix.decision.support.round
import kotlin.math.ln
import kotlin.math.sqrt

/** One choice the learner can pick, with an optional prior. */
@ConsistentCopyVisibility
data class Arm private constructor(
    val id: String,
    val priorMean: Double,
    val priorWeight: Double,
    val cost: Double,
    val risk: Double,
) {
    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "id" to id,
            "prior_mean" to priorMean,
            "prior_weight" to priorWeight,
            "cost" to cost,
            "risk" to risk,
        )

    companion object {
        operator fun invoke(
            id: String,
            priorMean: Double = 0.5,
            priorWeight: Double = 1.0,
            cost: Double = 0.0,
            risk: Double = 0.0,
        ): Arm = create(id, clamp(priorMean), maxOf(0.0, priorWeight), cost, risk)

        private fun create(
            id: String,
            priorMean: Double,
            priorWeight: Double,
            cost: Double,
            risk: Double,
        ): Arm = Arm(
            id = id,
            priorMean = priorMean,
            priorWeight = priorWeight,
            cost = cost,
            risk = risk,
        )
    }
}

/**
 * Map a measured outcome label to a reward in `0..1`.
 *
 * `unknown` returns `null`: the learner skips it rather than inventing a reward.
 */
fun rewardForLabel(label: String?): Double? =
    when ((label ?: "").trim().lowercase()) {
        "helped" -> 1.0
        "neutral" -> 0.5
        "hurt" -> 0.0
        else -> null
    }

/**
 * A deterministic upper-confidence-bound learner over named arms.
 *
 * UCB is used instead of Thompson sampling so replay and tests are stable. An
 * arm that has never been pulled is explored first.
 */
class UCBBandit(
    arms: Iterable<Arm> = emptyList(),
    exploration: Double = 1.4,
) {
    val exploration: Double = maxOf(0.0, exploration)

    private val arms = LinkedHashMap<String, Arm>()
    private val pulls = LinkedHashMap<String, Int>()
    private val rewards = LinkedHashMap<String, Double>()

    init {
        for (arm in arms) add(arm)
    }

    fun add(arm: Arm) {
        val name = arm.id.trim()
        require(name.isNotEmpty()) { "arm id is required" }
        arms[name] = arm
        pulls.putIfAbsent(name, 0)
        rewards.putIfAbsent(name, 0.0)
    }

    fun arms(): List<Arm> = arms.values.toList()

    fun get(armId: String): Arm =
        arms[armId] ?: throw NoSuchElementException("unknown arm '$armId'")

    fun update(armId: String, reward: Double): Arm {
        get(armId)
        pulls[armId] = pulls.getValue(armId) + 1
        rewards[armId] = rewards.getValue(armId) + clamp(reward)
        return get(armId)
    }

    /** Update from labelled outcomes; return how many were used. */
    fun learn(outcomes: Iterable<Outcome>, armOf: (String) -> String): Int {
        var used = 0
        for (outcome in outcomes) {
            val reward = rewardForLabel(outcome.label) ?: continue
            update(armOf(outcome.decisionId), reward)
            used++
        }
        return used
    }

    fun pulls(armId: String): Int {
        get(armId)
        return pulls.getValue(armId)
    }

    fun mean(armId: String): Double {
        val arm = get(armId)
        val count = pulls.getValue(armId)
        val total = arm.priorMean * arm.priorWeight + rewards.getValue(armId)
        return clamp(total / maxOf(arm.priorWeight + count, 1e-9))
    }

    fun score(armId: String): Double {
        get(armId)
        val count = pulls.getValue(armId)
        if (count == 0) return Double.POSITIVE_INFINITY
        val total = pulls.values.sum()
        val bonus = exploration * sqrt(ln(total + 1.0) / count)
        return mean(armId) + bonus
    }

    fun choose(
        maxRisk: Double = 1.0,
        budget: Double = Double.POSITIVE_INFINITY,
        exclude: Collection<String> = emptyList(),
    ): Arm? {
        val blocked = exclude.toSet()
        val candidates = arms.values.filter {
            it.id !in blocked && it.risk <= maxRisk && it.cost <= budget
        }
        return candidates.maxByOrNull { score(it.id) }
    }

    fun toMap(): Map<String, Any?> =
        linkedMapOf(
            "exploration" to exploration,
            "arms" to arms.values.map {
                it.toMap() + mapOf(
                    "pulls" to pulls.getValue(it.id),
                    "mean" to round(mean(it.id), 6),
                )
            },
        )
}
