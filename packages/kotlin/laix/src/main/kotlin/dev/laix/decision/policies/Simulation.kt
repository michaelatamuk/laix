package dev.laix.decision.policies

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.contracts.Decision
import dev.laix.decision.contracts.DecisionRequest

/** Where the shadow policy disagreed with the primary. */
data class ShadowDifference(
    val request: DecisionRequest,
    val primary: List<Decision>,
    val shadow: List<Decision>,
)

/** Run a policy over recorded requests; no side effects. */
fun simulate(policy: DecisionPolicy, requests: List<DecisionRequest>): List<List<Decision>> =
    requests.map { policy.decide(it) }

/** Return the primary decision and record every disagreement. */
class ShadowPolicy(
    val primary: DecisionPolicy,
    val shadow: DecisionPolicy,
    override val name: String = "shadow.v1",
) : DecisionPolicy {
    val version: String = name
    val differences: MutableList<ShadowDifference> = mutableListOf()

    override fun decide(request: DecisionRequest): List<Decision> {
        val primaryDecisions = primary.decide(request)
        val shadowDecisions = shadow.decide(request)
        if (signature(primaryDecisions) != signature(shadowDecisions)) {
            differences += ShadowDifference(
                request = request,
                primary = primaryDecisions,
                shadow = shadowDecisions,
            )
        }
        return primaryDecisions
    }

    private fun signature(decisions: List<Decision>): List<Triple<String, String?, String>> =
        decisions.map { Triple(it.verb.value, it.actionId, it.reasonCode) }
}
