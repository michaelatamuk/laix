package dev.laix.decision.policies.packs

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest
import dev.laix.decision.contracts.Intent
import dev.laix.decision.contracts.Verb
import dev.laix.decision.learning.bandit.Arm
import dev.laix.decision.learning.bandit.UCBBandit
import dev.laix.decision.support.truthy

/**
 * A learned policy: choose the arm the outcomes say is working.
 *
 * [BanditPolicy] puts the UCB learner behind the policy interface. It reads
 * generic arms from the request attributes or from the bandit itself, picks the
 * best arm inside the risk and budget limits, and accepts outcome rewards so
 * the next decision improves.
 */
class BanditPolicy(
    val bandit: UCBBandit = UCBBandit(exploration = 1.4),
    val maxRisk: Double = 1.0,
    val budget: Double = Double.POSITIVE_INFINITY,
) : DecisionPolicy {
    override val name: String = "bandit.v1"
    override val version: String = "0.8.0"

    override fun decide(request: DecisionRequest): List<Decision> {
        for (item in policyList(policyValue(request, "arms"))) {
            val parsed = when (item) {
                is Arm -> item
                is Map<*, *> -> arm(item.entries.associate { it.key.toString() to it.value })
                else -> continue
            }
            bandit.add(parsed)
        }

        if (bandit.arms().isEmpty()) {
            return listOf(
                policyDecision(name, Verb.WAIT, "no_arms", "the learner has no arm to choose", 0.5),
            )
        }

        val chosen = bandit.choose(
            maxRisk = policyNumber(request, "max_risk", maxRisk),
            budget = policyNumber(request, "budget", budget),
            exclude = (policyValue(request, "exclude") as? Iterable<*>)?.map { it.toString() }
                ?: emptyList(),
        )
        if (chosen == null) {
            return listOf(
                policyDecision(
                    name,
                    Verb.WAIT,
                    "no_arm_within_limits",
                    "every arm breaks the risk or budget limit",
                    0.7,
                ),
            )
        }

        val mean = bandit.mean(chosen.id)
        return listOf(
            policyDecision(
                name,
                Verb.ACT,
                "bandit_choice",
                String.format(
                    java.util.Locale.ROOT,
                    "choose arm %s with learned reward %.2f",
                    chosen.id,
                    mean,
                ),
                minOf(0.98, 0.5 + mean * 0.4),
                intent = Intent("act", mapOf("arm" to chosen.id)),
                score = round6(mean),
                requiresApproval = truthy(policyValue(request, "requires_approval", false)),
                actionId = chosen.id,
            ),
        )
    }

    /** Record one reward in `0..1` for an arm. */
    fun record(armId: String, reward: Double): Arm = bandit.update(armId, reward)

    /** Learn from labelled outcomes; [armOf] maps a decision id to an arm. */
    fun learn(
        outcomes: Iterable<dev.laix.decision.outcomes.Outcome>,
        armOf: (String) -> String,
    ): Int = bandit.learn(outcomes, armOf)

    private fun arm(item: Map<String, Any?>): Arm =
        Arm(
            id = mapText(item, "id"),
            priorMean = mapNumber(item, "prior_mean", 0.5),
            priorWeight = mapNumber(item, "prior_weight", 1.0),
            cost = mapNumber(item, "cost"),
            risk = mapNumber(item, "risk"),
        )
}
