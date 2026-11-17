package dev.laix.decision.policies

import dev.laix.decision.contract.DecisionPolicy
import dev.laix.decision.support.DecisionPolicyError

/** A small name-to-policy map used by `DecisionClient`. */
class DecisionPolicyRegistry {
    private val policies = LinkedHashMap<String, DecisionPolicy>()

    fun register(name: String, policy: DecisionPolicy) {
        val key = name.trim()
        if (key.isEmpty()) throw DecisionPolicyError("policy name is required")
        policies[key] = policy
    }

    fun get(name: String): DecisionPolicy =
        policies[name] ?: throw DecisionPolicyError(
            "unknown policy '$name'; registered: ${names().joinToString(", ").ifEmpty { "none" }}",
        )

    fun names(): List<String> = policies.keys.sorted()
}
